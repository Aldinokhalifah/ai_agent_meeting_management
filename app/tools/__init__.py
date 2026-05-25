from tools.meeting_tools import MEETING_TOOLS, execute_meeting_tool
from tools.participant_tools import PARTICIPANT_TOOLS, execute_participant_tool
from tools.action_item_tools import ACTION_ITEM_TOOLS, execute_action_item_tool
from tools.info_tools import INFO_TOOLS, execute_info_tool
from tools.continuation_tools import CONTINUATION_TOOLS, execute_continuation_tool

def get_all_tools():
    """Return semua tool definitions untuk dikirim ke LLM"""
    return [
        *MEETING_TOOLS,
        *PARTICIPANT_TOOLS,
        *ACTION_ITEM_TOOLS,
        *INFO_TOOLS,
        *CONTINUATION_TOOLS
    ]

async def execute_tool(tool_name: str, args: dict):
    """Router — pilih executor yang tepat berdasarkan nama tool"""

    meeting_tool_names = [t["function"]["name"] for t in MEETING_TOOLS]
    participant_tool_names = [t["function"]["name"] for t in PARTICIPANT_TOOLS]
    action_item_tool_names = [t["function"]["name"] for t in ACTION_ITEM_TOOLS]
    info_tool_names = [t["function"]["name"] for t in INFO_TOOLS]
    continuation_tool_names = [t["function"]["name"] for t in CONTINUATION_TOOLS]
    
    if tool_name in meeting_tool_names:
        return await execute_meeting_tool(tool_name, args)
    elif tool_name in participant_tool_names:
        return await execute_participant_tool(tool_name, args)
    elif tool_name in action_item_tool_names:
        return await execute_action_item_tool(tool_name, args)
    elif tool_name in info_tool_names:
        return await execute_info_tool(tool_name, args)
    elif tool_name in continuation_tool_names:
        return await execute_continuation_tool(tool_name, args)
    else:
        raise ValueError(f"Tool '{tool_name}' tidak ditemukan")