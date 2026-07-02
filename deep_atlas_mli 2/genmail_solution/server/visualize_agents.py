"""
Visualize LangGraph agent workflows as interactive diagrams.

Usage:
    # Visualize all agents
    uv run python visualize_agents.py
    
    # Visualize a specific agent
    uv run python visualize_agents.py --agent task_extractor
    uv run python visualize_agents.py --agent reply_drafter
    
    # List available agents
    uv run python visualize_agents.py --list

This will generate:
- Mermaid markdown files (.md)
- Interactive HTML visualizations (.html)
- PNG images (if graphviz is installed)
"""

import argparse
from typing import Dict, Any
from pathlib import Path

from agents.task_extractor import create_workflow as create_task_workflow, AgentState as TaskState
from agents.reply_drafter import create_workflow as create_reply_workflow, ReplyState


# Registry of available agents
AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "task_extractor": {
        "name": "Task Extractor Agent",
        "description": "Extracts actionable tasks from unread emails",
        "create_workflow": create_task_workflow,
        "state_type": TaskState,
        "module": "agents.task_extractor"
    },
    "reply_drafter": {
        "name": "Reply Drafter Agent",
        "description": "Drafts email replies based on thread context",
        "create_workflow": create_reply_workflow,
        "state_type": ReplyState,
        "module": "agents.reply_drafter"
    }
}


def get_node_info(graph, node_name: str) -> Dict[str, Any]:
    """Extract information about a node from the graph"""
    try:
        nodes = graph.get_graph().nodes
        if node_name in nodes:
            node = nodes[node_name]
            return {
                "name": node_name,
                "type": type(node).__name__ if hasattr(node, '__class__') else "Unknown",
            }
    except Exception:
        pass
    return {"name": node_name}


def get_state_fields(state_type) -> list:
    """Extract state field information from TypedDict"""
    fields = []
    if hasattr(state_type, '__annotations__'):
        for field_name, field_type in state_type.__annotations__.items():
            # Get the type string
            type_str = str(field_type)
            # Clean up Optional[] wrapper
            if "Optional" in type_str:
                type_str = type_str.replace("Optional[", "").replace("]", "")
            if "typing." in type_str:
                type_str = type_str.split(".")[-1]
            fields.append({
                "name": field_name,
                "type": type_str,
                "optional": "Optional" in str(field_type)
            })
    return fields


def save_mermaid(graph, filename: str, agent_info: Dict[str, Any]):
    """Save graph as Mermaid markdown"""
    mermaid = graph.get_graph().draw_mermaid()

    output_path = Path(filename + ".md")
    with open(output_path, "w") as f:
        f.write(f"# {agent_info['name']} - Workflow Visualization\n\n")
        f.write(f"**Description:** {agent_info['description']}\n\n")
        f.write("## Graph Structure\n\n")
        f.write("```mermaid\n")
        f.write(mermaid)
        f.write("\n```\n\n")
        
        # Add state information
        if agent_info.get('state_type'):
            f.write("## State Schema\n\n")
            fields = get_state_fields(agent_info['state_type'])
            f.write("| Field | Type | Optional |\n")
            f.write("|-------|------|----------|\n")
            for field in fields:
                optional = "Yes" if field['optional'] else "No"
                f.write(f"| `{field['name']}` | `{field['type']}` | {optional} |\n")
            f.write("\n")

    print(f"✓ Saved Mermaid diagram: {output_path}")
    return mermaid


def save_html(graph, filename: str, agent_info: Dict[str, Any], mermaid_code: str):
    """Save interactive HTML visualization"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agent_info['name']} - LangGraph Visualization</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-top: 0;
        }}
        .description {{
            color: #666;
            font-size: 1.1em;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}
        .mermaid-container {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            border: 1px solid #ddd;
            margin: 20px 0;
        }}
        .state-schema {{
            margin-top: 30px;
        }}
        .state-schema h2 {{
            color: #333;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .type-badge {{
            display: inline-block;
            padding: 2px 8px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .optional {{
            color: #666;
            font-style: italic;
        }}
        .info-box {{
            background: #f0f7ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{agent_info['name']}</h1>
        <div class="description">{agent_info['description']}</div>
        
        <div class="info-box">
            <strong>Module:</strong> <code>{agent_info['module']}</code><br>
            <strong>Visualization Type:</strong> LangGraph StateGraph
        </div>
        
        <h2>Workflow Graph</h2>
        <div class="mermaid-container">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>
"""
    
    # Add state schema if available
    if agent_info.get('state_type'):
        fields = get_state_fields(agent_info['state_type'])
        html_content += """
        <div class="state-schema">
            <h2>State Schema</h2>
            <p>The state object passed between nodes:</p>
            <table>
                <thead>
                    <tr>
                        <th>Field</th>
                        <th>Type</th>
                        <th>Optional</th>
                    </tr>
                </thead>
                <tbody>
"""
        for field in fields:
            optional_text = "Yes" if field['optional'] else "No"
            optional_class = "optional" if field['optional'] else ""
            html_content += f"""
                    <tr>
                        <td><code>{field['name']}</code></td>
                        <td><span class="type-badge">{field['type']}</span></td>
                        <td class="{optional_class}">{optional_text}</td>
                    </tr>
"""
        html_content += """
                </tbody>
            </table>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    output_path = Path(filename + ".html")
    with open(output_path, "w") as f:
        f.write(html_content)
    
    print(f"✓ Saved HTML visualization: {output_path}")


def save_png(graph, filename: str):
    """Save graph as PNG image (requires graphviz)"""
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        output_path = Path(filename + ".png")
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        print(f"✓ Saved PNG image: {output_path}")
        return True
    except ImportError:
        print(f"⚠ Skipping PNG (install: pip install pygraphviz)")
        return False
    except Exception as e:
        print(f"⚠ Could not generate PNG: {e}")
        return False


def visualize_agent(agent_key: str, output_dir: str = "."):
    """Visualize a specific agent"""
    if agent_key not in AGENT_REGISTRY:
        print(f"❌ Error: Unknown agent '{agent_key}'")
        print(f"Available agents: {', '.join(AGENT_REGISTRY.keys())}")
        return False
    
    agent_info = AGENT_REGISTRY[agent_key]
    print(f"\n{'='*60}")
    print(f"Visualizing: {agent_info['name']}")
    print(f"{'='*60}")
    print(f"Description: {agent_info['description']}\n")
    
    try:
        # Create the workflow
        workflow = agent_info['create_workflow']()
        graph = workflow.get_graph()
        
        # Generate output files
        output_path = Path(output_dir) / f"{agent_key}_graph"
        mermaid = save_mermaid(workflow, str(output_path), agent_info)
        save_html(workflow, str(output_path), agent_info, mermaid)
        save_png(workflow, str(output_path))
        
        print(f"\n✓ Successfully generated visualizations for {agent_info['name']}")
        return True
        
    except Exception as e:
        print(f"❌ Error visualizing agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def visualize_all(output_dir: str = "."):
    """Generate visualizations for all agents"""
    print("Generating visualizations for all LangGraph agents...\n")
    
    success_count = 0
    for agent_key in AGENT_REGISTRY.keys():
        if visualize_agent(agent_key, output_dir):
            success_count += 1
        print()
    
    print("="*60)
    print(f"Completed: {success_count}/{len(AGENT_REGISTRY)} agents visualized")
    print("="*60)
    print("\nGenerated files:")
    print("  - *_graph.md (Mermaid markdown)")
    print("  - *_graph.html (Interactive HTML)")
    print("  - *_graph.png (PNG image, if available)")
    print("\nView HTML files in your browser or Mermaid diagrams at:")
    print("  https://mermaid.live/")


def list_agents():
    """List all available agents"""
    print("Available LangGraph Agents:\n")
    for key, info in AGENT_REGISTRY.items():
        print(f"  {key}")
        print(f"    Name: {info['name']}")
        print(f"    Description: {info['description']}")
        print(f"    Module: {info['module']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize LangGraph agent workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python visualize_agents.py                    # Visualize all agents
  python visualize_agents.py --agent task_extractor  # Visualize specific agent
  python visualize_agents.py --list             # List available agents
        """
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Visualize a specific agent (use --list to see available agents)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available agents"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Output directory for generated files (default: current directory)"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_agents()
    elif args.agent:
        visualize_agent(args.agent, args.output_dir)
    else:
        visualize_all(args.output_dir)


if __name__ == "__main__":
    main()
