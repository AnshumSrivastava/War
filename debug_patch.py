import sys

def patch_refresh_roster():
    from ui.tools.place_agent_tool import PlaceAgentTool
    old_method = PlaceAgentTool.refresh_roster
    def new_refresh_roster(self):
        print(f"DEBUG: Entering refresh_roster. list_widget={self.list_widget}")
        try:
            old_method(self)
        except Exception as e:
            print(f"DEBUG: EXCEPTION in refresh_roster = {e}")
            import traceback
            traceback.print_exc()
        print("DEBUG: Exiting refresh_roster.")
    PlaceAgentTool.refresh_roster = new_refresh_roster

patch_refresh_roster()
