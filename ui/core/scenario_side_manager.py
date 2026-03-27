"""
FILE: ui/core/scenario_side_manager.py
ROLE: The "Diplomat".

DESCRIPTION:
This controller manages the assignment of map sections to different sides 
(Red/Blue/Neutral) and handles scenario-specific sub-tab changes.
"""
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QCursor
from ui.dialogs.themed_dialogs import ThemedMessageBox

class ScenarioSideManager(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.state = main_window.state
        self.detected_sections = []
        self.section_assignments = {}
        
    def start_side_assignment(self):
        """Detects sections and enters side assignment mode."""
        self.mw.log_info("Starting Side Assignment...")
        self.detected_sections = self.state.map.detect_sections() 
        
        if len(self.detected_sections) < 2:
            ThemedMessageBox.warning(self.mw, "Invalid Border", 
                "The border doesn't split the map clearly. Draw an Edge-to-Edge line first.")
            return
            
        self.section_assignments = {}
        ThemedMessageBox.information(self.mw, "Assignment Mode", 
            f"Detected {len(self.detected_sections)} sections. Click on them to assign Red or Blue.")
            
        self.state.assign_sides_mode = True 
        self.mw.set_tool("cursor")
        
    def handle_section_click(self, hex_obj):
        """Handles a hex click during side assignment mode."""
        target_section = None
        t_h = tuple(hex_obj)
        
        for sec in self.detected_sections:
            if t_h in sec['hexes']:
                target_section = sec
                break
        
        if not target_section:
            self.mw.log_info("Clicked on Border or Invalid Hex.")
            return
            
        menu = QMenu(self.mw)
        sides = ["Red", "Blue", "Neutral"]
        
        for side in sides:
            a = menu.addAction(side)
            a.setData(side)
            
        res = menu.exec_(QCursor.pos())
        if res:
            side_choice = res.data()
            self.section_assignments[target_section['id']] = side_choice
            self.mw.log_info(f"Assigned Section {target_section['id']} to <b>{side_choice}</b>")
            self.check_auto_assign()

    def check_auto_assign(self):
        """Auto-assigns the last section if the result is obvious."""
        total = len(self.detected_sections)
        assigned = len(self.section_assignments)
        
        if assigned == total:
            self.finalize_assignments()
            return
            
        if total - assigned == 1:
            used_sides = set(self.section_assignments.values())
            missing_side = None
            if "Red" in used_sides and "Blue" not in used_sides:
                missing_side = "Blue"
            elif "Blue" in used_sides and "Red" not in used_sides:
                missing_side = "Red"
                
            if missing_side:
                for sec in self.detected_sections:
                    if sec['id'] not in self.section_assignments:
                        self.section_assignments[sec['id']] = missing_side
                        self.mw.log_info(f"Auto-assigned Section {sec['id']} to <b>{missing_side}</b>")
                        ThemedMessageBox.information(self.mw, "Auto-Assign", 
                            f"Only one section left. Auto-assigned to {missing_side}.")
                        self.finalize_assignments()
                        return

    def finalize_assignments(self):
        """Commits side assignments to the map state."""
        from PyQt5.QtWidgets import QMessageBox
        res = ThemedMessageBox.question(self.mw, "Finalize", "All sections assigned. Finish setup?", 
            QMessageBox.Yes | QMessageBox.No)
            
        if res == QMessageBox.Yes:
            self.state.map.hex_sides = {}
            border_set = set(tuple(h) for h in self.state.map.border_path)
            
            for h in border_set:
                self.state.map.hex_sides[h] = "Border"
                
            for sec in self.detected_sections:
                sid = sec['id']
                side = self.section_assignments.get(sid, "Neutral")
                for h_t in sec['hexes']:
                    self.state.map.hex_sides[h_t] = side
            
            self.state.assign_sides_mode = False
            self.mw.set_tool("place_agent")
            ThemedMessageBox.information(self.mw, "Done", "Scenario Sides Configured.\nReady to place units.")

    def on_scenario_side_tab_changed(self, index):
        """Handles sub-tab switching (Attacker/Defender/Combined/Rules)."""
        sides = ["Attacker", "Defender", "Combined", "Rules"]
        if index < len(sides):
            side = sides[index]
            self.state.active_scenario_side = side
            self.mw.log_info(f"Scenario Focus: <b>{side.upper()}</b>")
            
            if hasattr(self.mw, 'toolbar_controller'):
                self.mw.toolbar_controller.update_tools_visibility()
            else:
                self.mw.update_tools_visibility()
            
            if hasattr(self.mw, 'scenario_manager_group'):
                self.mw.scenario_manager_group.refresh_list()
