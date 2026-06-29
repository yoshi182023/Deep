# Adapted from https://pytorch.org/serve/custom_service.html#custom-handler-with-class-level-entry-point

# Import the required libraries
import base64
import io
from PIL import Image
import torch
import clip
from ts.torch_handler.base_handler import BaseHandler
from ts.handler_utils.timer import timed


class Handler(BaseHandler):
    """
    This class extends the BaseHandler class from Torchserve. The methods within will shadow the default methods in the BaseHandler class, allowing us to customize the behavior of the handler.

    In turn, BaseHandler will run the methods in the following order to perform inference for each request: initialize() -> preprocess() -> inference() -> postprocess()

    The rest of the request-handling, logging, metrics-tracking and error-handling is handled by Torchserve.
    """

    def __init__(self):
        # The constructor is responsible for initializing the handler and setting up necessary elements like the model, preprocessing steps, and labels.
        self._context = None
        self.initialized = False
        self.explain = False
        self.target = 0
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Custom labels that we want CLIP to classify images into
        self.labels = ["coffee", "toast", "other"]
        try:
            # Initialize the model
            self.model, self.clip_preprocess = clip.load(
                "./ViT-B-32.pt", device=self.device
            )
            # Tokenize the labels so that CLIP can compare them to the image embeddings
            self.text = clip.tokenize(self.labels).to(self.device)

        except Exception as e:
            print(
                "An exception occurred while loading CLIP and tokenizing labels:",
                e,
            )

    def initialize(self, context):
        # This method is called when the model is loaded. It can be used to perform other initialization steps. Torchserve requires that self._context is defined and that the self.initialized flag is set to True before inference can be performed.
        self._context = context
        self.initialized = True

    @timed
    def preprocess(self, data):
        # This method is responsible for preprocessing the input data before it is passed to the model for inference.
        try:
            # Get the image data from the request
            image_data = data[0].get("data") or data[0].get("body")

            # Convert the image data to a PIL image or a tensor
            if isinstance(image_data, str):
                image = base64.b64decode(image_data)
            elif isinstance(image_data, (bytearray, bytes)):
                image = Image.open(io.BytesIO(bytes(image_data)))
            else:
                image = torch.FloatTensor(image_data)

            # Run .unsqueeze(0) to turn this single input into a "batch" of size 1 as this is what the model expects
            image = self.clip_preprocess(image).unsqueeze(0).to(self.device)

            return image

        except Exception as e:
            print("An exception occurred while preprocessing the image:", e)

    @timed
    def inference(self, image):
        # This method is responsible for running the model on the preprocessed data and returning the output.
        try:
            with torch.no_grad():
                # Generate raw similarity scores for each label, compared to the image
                logits_per_image, _ = self.model(image, self.text)
                # Scale the raw scores into probabilities (0-1)
                probabilities = (
                    logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                )
                # Create a dictionary of the probabilities for each label
                answer = {
                    # Convert to string for JSON serialization
                    label: str(prob)
                    for label, prob in zip(self.labels, probabilities)
                }
                return answer

        except Exception as e:
            print("An exception occurred in inference", e)

    @timed
    def postprocess(self, data):
        # This method is responsible for postprocessing the output of the model before it is returned to the client. Here, we are wrapping the output in a list so that Torchserve can prepare a batch inference response. We could also use this method to perform other postprocessing steps like decoding the predictions or applying a threshold.
        print("Classification: ", data)
        return [data]
