

def format_table(title, data):
    """
    Formats a list of dictionaries (or a single dict) into a text table.
    Legacy support.
    """
    if not data:
        return f"\n--- {title} ---\n(No Data)\n"
    
    # Normalize to list of dicts
    if isinstance(data, dict):
        rows = [{"Key": k, "Value": str(v)} for k, v in data.items()]
        headers = ["Key", "Value"]
    elif isinstance(data, list):
        if not data: return f"\n--- {title} ---\n(Empty List)\n"
        headers = list(data[0].keys())
        rows = []
        for item in data:
            row = {}
            for h in headers:
                val = item.get(h, "")
                row[h] = str(val)
            rows.append(row)
    else:
        return f"\n--- {title} ---\n{str(data)}\n"

    # Calculate column widths
    col_widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(row[h]))
    
    def pad(text, width):
        return text + " " * (width - len(text))

    lines = []
    lines.append(f"\n=== {title} ===")
    header_line = "| " + " | ".join([pad(h, col_widths[h]) for h in headers]) + " |"
    lines.append("-" * len(header_line))
    lines.append(header_line)
    lines.append("-" * len(header_line))
    for row in rows:
        row_line = "| " + " | ".join([pad(row[h], col_widths[h]) for h in headers]) + " |"
        lines.append(row_line)
    lines.append("-" * len(header_line))
    return "\n".join(lines)


def format_html_log(title, data):
    """
    Formats a list of agent step data into a rich HTML table.
    
    Args:
        title (str): Log title.
        data (list[dict]): List of dicts containing:
            - Agent, Side, HP, Pos, Target, Action, Reward, State, Thinking (optional)
            
    Returns:
        str: HTML string.
    """
    if not data:
        return f"<h3>{title}</h3><p>(No Agents Active)</p>"

    # Table Header
    html = f"""
    <div style="margin-bottom: 20px;">
        <h3 style="color: #ffffff; margin: 0; padding: 5px; background-color: #333;">{title}</h3>
        <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 1.1em;">
            <tr style="background-color: #444; color: #ddd; text-align: left;">
                <th style="padding: 4px;">Agent</th>
                <th style="padding: 4px;">HP</th>
                <th style="padding: 4px;">Pos</th>
                <th style="padding: 4px;">Action</th>
                <th style="padding: 4px;">Reward</th>
                <th style="padding: 4px;">Thinking</th>
            </tr>
    """

    for row_idx, item in enumerate(data):
        # Determine Styles
        bg_color = "#2a2a2a" if row_idx % 2 == 0 else "#222222"
        
        side = item.get("Side", "?")
        name_color = "#ff6b6b" if side == "Attacker" else "#4dabf7" # Red / Blue
        if side == "Neutral": name_color = "#cccccc"
        
        # Reward Color
        try:
            rew_val = float(item.get("Reward", 0))
            if rew_val > 0: rew_color = "#69db7c" # Green
            elif rew_val < 0: rew_color = "#ff8787" # Red
            else: rew_color = "#888"
        except:
            rew_color = "#888"

        # Content
        agent_name = item.get("Agent", "Unknown")
        # Support both 'HP' (legacy/UI) and 'Personnel' (V3 engine)
        hp = item.get("HP", item.get("Personnel", "0"))
        pos = item.get("Pos", "")
        action = item.get("Action", "")
        thinking = item.get("Thinking", "")
        state_info = item.get("State", "") # Optional state info

        # Thinking Cell: Combine State + Q-Values
        think_html = ""
        # Ensure state info (from encoder) is displayed first
        if state_info:
            think_html += f"<div style='color: #eee; font-size: 0.9em; margin-bottom: 4px; background: #444; padding: 2px;'>{state_info}</div>"
        if thinking:
            think_html += f"<div style='color: #aaa; font-size: 0.85em;'>{thinking}</div>"
        if not think_html:
            think_html = "<span style='color: #666;'>No Debug Data</span>"

        html += f"""
            <tr style="background-color: {bg_color}; border-bottom: 1px solid #333;">
                <td style="padding: 6px; color: {name_color}; font-weight: bold;">
                    {agent_name}<br>
                    <span style="font-size: 0.8em; color: #666;">{item.get('Type','')}</span>
                </td>
                <td style="padding: 6px; color: #ddd;">{hp}</td>
                <td style="padding: 6px; color: #bbb;">{pos}</td>
                <td style="padding: 6px; color: #fff; font-weight: bold;">{action}</td>
                <td style="padding: 6px; color: {rew_color}; font-weight: bold;">{item.get('Reward','0')}</td>
                <td style="padding: 6px;">{think_html}</td>
            </tr>
        """

    html += "</table></div>"
    return html
