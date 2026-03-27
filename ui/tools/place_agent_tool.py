"""
FILE: ui/tools/place_agent_tool.py
ROLE: The "Unit Recruiter" (Deployment Tool).

DESCRIPTION:
This tool allows you to place units (agents) onto the battlefield.
It handles several important rules:
1. It automatically picks a name for the unit based on its team (Attacker/Defender).
2. It checks if the team has reached its "Force Limit" (max units allowed).
3. It prevents you from placing units in enemy territory or in empty "Void" space.

It uses the game's Master Database to determine how strong and fast each 
unit type should be.
"""

from .base_tool import MapTool
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, QGroupBox, 
                             QLineEdit, QPushButton, QRadioButton, QButtonGroup, QHBoxLayout)
from engine.core.entity_manager import Agent
import os
import json

class PlaceAgentTool(MapTool):
    """
    Handles the logic for selecting and spawning new units on the map.
    """
    def __init__(self, widget):
        super().__init__(widget)
        self.lbl_side = None
        self.radio_attacker = None
        self.radio_defender = None
        self.side_group = None
        self.combo_identity = None
        self.btn_refresh = None
        self.combo_type = None
        self.combo_subtype = None
        self.agent_templates = {}
        self._active = False

    def activate(self):
        self._active = True
        super().activate()

    def deactivate(self):
        self._active = False
        super().deactivate()

    def get_options_widget(self):
        """
        THE RECRUITMENT DESK: Builds the UI panel in the sidebar where you 
        pick which unit to place.
        """
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Side Display ---
        # Reminds you which team you are currently placing units for.
        self.lbl_side = QLabel(f"Side: <b>Unknown</b>")
        self.lbl_side.setStyleSheet("font-size: 14px; padding: 5px;")
        
        radio_widget = QWidget()
        radio_layout = QHBoxLayout(radio_widget)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        self.radio_attacker = QRadioButton("Attacker")
        self.radio_defender = QRadioButton("Defender")
        self.side_group = QButtonGroup()
        self.side_group.addButton(self.radio_attacker)
        self.side_group.addButton(self.radio_defender)
        
        radio_layout.addWidget(self.radio_attacker)
        radio_layout.addWidget(self.radio_defender)
        
        self.radio_attacker.toggled.connect(self.on_side_radio_toggled)
        self.radio_defender.toggled.connect(self.on_side_radio_toggled)
        
        layout.addWidget(self.lbl_side)
        layout.addWidget(radio_widget)
        
        # --- Unit Identity ---
        group = QGroupBox("Unit Identity")
        v_layout = QVBoxLayout()
        
        self.combo_identity = QComboBox() # The dropdown/text box for the unit's name.
        self.btn_refresh = QPushButton("Refresh Roster") # Button to clear and rebuild the list.
        self.btn_refresh.clicked.connect(self.refresh_roster)
        
        v_layout.addWidget(QLabel("Select Agent:"))
        v_layout.addWidget(self.combo_identity)
        v_layout.addWidget(self.btn_refresh)
        
        group.setLayout(v_layout)
        layout.addWidget(group)

        # --- Unit Class Selection ---
        type_group = QGroupBox("Class / Loadout")
        t_layout = QVBoxLayout()
        
        self.combo_type = QComboBox()    # Main type (e.g. Infantry).
        self.combo_subtype = QComboBox() # Specialization (e.g. Sniper).
        
        self.combo_type.setEditable(False)
        self.combo_subtype.setEditable(False)
        self.agent_templates = {} # Stores the stats for each unit type.
        
        self.combo_subtype.clear()
        self.combo_subtype.addItem("Standard")
        self.state.place_opt_subtype = "Standard"

        self.combo_type.currentTextChanged.connect(self._on_type_changed)
        t_layout.addWidget(QLabel("Type:"))
        t_layout.addWidget(self.combo_type)
        t_layout.addWidget(QLabel("Subtype:"))
        t_layout.addWidget(self.combo_subtype)
        type_group.setLayout(t_layout)
        layout.addWidget(type_group)
        
        widget.setLayout(layout)
        
        # Wait a split second for everything to initialize before loading the unit list.
        QTimer.singleShot(100, self.refresh_roster)
        
        return widget

    def on_side_radio_toggled(self):
        # Only update if the scenario side is Combined
        if not self._active: return
        side = getattr(self.state, "active_scenario_side", "Attacker")
        if side == "Combined":
             new_side = "Attacker" if self.radio_attacker.isChecked() else "Defender"
             self.refresh_roster_for_side(new_side)

    def _on_type_changed(self, text):
        if not self._active: return
        side = getattr(self.state, "active_scenario_side", "Attacker")
        if side == "Combined":
            side = "Attacker" if self.radio_attacker and self.radio_attacker.isChecked() else "Defender"
        self.refresh_roster_for_side(side)

    def refresh_roster(self):
        """
        UNIT LIST GENERATOR: Scans the map to see who is already placed 
        and suggests the next unit name in sequence.
        """
        if not self._active: return
        
        try:
            # 1. Identify which side we are building (Attacker or Defender).
            side = getattr(self.state, "active_scenario_side", "Attacker")
            
            if side == "Combined":
                if self.lbl_side: self.lbl_side.setText(f"Side: <b>Select Below</b>")
                if self.radio_attacker: self.radio_attacker.setEnabled(True)
                if self.radio_defender: self.radio_defender.setEnabled(True)
                
                # Default to checking one if neither are checked
                if self.radio_attacker and not self.radio_attacker.isChecked() and self.radio_defender and not self.radio_defender.isChecked():
                    # Block signals to avoid double calling refresh
                    self.radio_attacker.blockSignals(True)
                    self.radio_attacker.setChecked(True)
                    self.radio_attacker.blockSignals(False)
                
                active_side = "Attacker" if self.radio_attacker and self.radio_attacker.isChecked() else "Defender"
                self.refresh_roster_for_side(active_side)
            else:
                if self.lbl_side: self.lbl_side.setText(f"Side: <b>{side}</b>")
                if self.radio_attacker: self.radio_attacker.setEnabled(False)
                if self.radio_defender: self.radio_defender.setEnabled(False)
                
                # Set the radio button to match the fixed side
                if self.radio_attacker and self.radio_defender:
                    self.radio_attacker.blockSignals(True)
                    self.radio_defender.blockSignals(True)
                    if side == "Attacker":
                        self.radio_attacker.setChecked(True)
                    else:
                        self.radio_defender.setChecked(True)
                    self.radio_attacker.blockSignals(False)
                    self.radio_defender.blockSignals(False)
                
                self.refresh_roster_for_side(side)
        except RuntimeError:
            # Widget already deleted, safe to ignore
            pass
            
    def refresh_roster_for_side(self, side):
        if not self._active: return
        
        try:
            # 2. Update the 'Type' list from the Master Database.
            self.combo_type.blockSignals(True)
            self.combo_type.clear()
            self.agent_templates = {}
            if hasattr(self.state, 'data_controller'):
                 agent_catalog = self.state.data_controller.agent_types.get(side, {})
                 if agent_catalog:
                      self.agent_templates = agent_catalog
                      self.combo_type.addItems(sorted(list(agent_catalog.keys())))
            
            if not self.agent_templates:
                 self.combo_type.addItem("No Agents Found in DB")
            self.combo_type.blockSignals(False)
            self.state.place_opt_type = self.combo_type.currentText()
            
            # 3. Find the next available sequence number for this unit type.
            # Names follow pattern: [B/R]_[Type]_[Number]
            prefix = "B" if side == "Attacker" else "R"
            unit_type = self.combo_type.currentText() or "Agent"
            
            existing_names = [ent.name for ent in self.state.entity_manager.get_all_entities()]
            
            idx = 1
            while True:
                suggested_name = f"{prefix}_{unit_type}_{idx}"
                if suggested_name not in existing_names:
                    break
                idx += 1
            
            # Fill the dropdown box with this suggestion.
            self.combo_identity.setEditable(True)
            self.combo_identity.clear()
            self.combo_identity.addItem(suggested_name, userData=suggested_name)
            self.combo_identity.setCurrentText(suggested_name)
        except RuntimeError:
            pass

    def on_subtype_changed(self, text):
        """Sets the specific role for the unit."""
        if text:
            self.state.place_opt_subtype = text

    def mousePressEvent(self, event):
        """Attempts to spawn a unit when you click on the map."""
        if event.button() == Qt.LeftButton:
            # Convert screen pixels to map coordinates.
            click_hex = self.widget.screen_to_hex(event.x(), event.y())
            
            # RULE: You cannot place units in the empty 'Void' outside the world.
            if not self.state.map.get_terrain(click_hex):
                print("Cannot place agent on void (invalid hex).")
                return
            
            # Determine which side (Red/Blue) is currently 'Active'.
            side = getattr(self.state, "active_scenario_side", "Attacker")
            if side == "Combined":
                side = "Attacker" if hasattr(self, "radio_attacker") and self.radio_attacker.isChecked() else "Defender"
            
            target_side = "Red" if side == "Attacker" else "Blue"
            
            # RULE: TERRITORY RESTRICTION. 
            # You usually cannot place units directly onto the enemy's starting territory.
            hex_side = self.state.map.hex_sides.get(tuple(click_hex))
            if hex_side:
                enemy_side = "Blue" if target_side == "Red" else "Red"
                if hex_side == enemy_side:
                    print(f"Cannot place {side} ({target_side}) on {hex_side} territory!")
                    self.log(f"Invalid Placement: {side} cannot enter {hex_side} zone.")
                    return 

            # --- MANPOWER LIMIT CHECK ---
            # 1. Count how many soldiers this team already has.
            current_count = 0
            for ent in self.state.entity_manager.get_all_entities():
                if ent.get_attribute("side") == side:
                    current_count += 1
            
            # 2. Get the recruitment limit from the scenario rules.
            rules = self.state.map.active_scenario.rules
            limit_key = "attacker_max_force" if side == "Attacker" else "defender_max_force"
            limit = rules.get(limit_key, 10) # If not set, limit is 10 units.
            
            # If we are at the limit, block the placement.
            if current_count >= limit:
                print(f"Max Force Limit Reached ({limit}) for {side}.")
                self.log(f"Cannot place: {side} Force Limit ({limit}) reached.")
                return
            
            # Retrieve the name the user typed or picked.
            try:
                identity = self.combo_identity.currentText().strip()
                if not identity:
                    print("Cannot place: Agent name is empty.")
                    return

                # RULE: NAMES MUST BE UNIQUE. No two units can have the same name.
                for ent in self.state.entity_manager.get_all_entities():
                    if ent.name == identity:
                        print(f"Agent {identity} already exists! Type a new name.")
                        return
                
                # Fetch the actual statistics (Personnel, Range, Speed) for this unit type 
                # from the Master Database.
                atype = self.combo_type.currentText()
                template = self.agent_templates.get(atype, {})
            except RuntimeError:
                return
            
            # --- THE BIRTH OF A UNIT ---
            agent = Agent(name=identity) 
            agent.set_attribute("side", side)
            
            asub = getattr(self.state, "place_opt_subtype", "Standard")
            agent.set_attribute("type", atype)
            agent.set_attribute("subtype", asub)
            
            # Map the database stats into the unit's actual attributes.
            caps = template.get("capabilities", {})
            if not caps and hasattr(self.state, 'data_controller'):
                # Resolve full config if template is minimal
                full_config = self.state.data_controller.resolve_unit_config(agent)
                agent.attributes.update({
                    "personnel": full_config.get("personnel", 100),
                    "movement": full_config.get("speed_of_action", 5.0),
                    "attack_range": full_config.get("range_of_fire", 3.0),
                    "combat_factor": full_config.get("combat_factor", 5.0),
                    "vision_range": full_config.get("vision_range", 6.0)
                })
            elif caps:
                agent.attributes.update({
                    "personnel": caps.get("attack", 100) * 4, # Scale personnel based on power.
                    "movement": caps.get("speed", 5),           # How many hexes it can move.
                    "attack_range": caps.get("range", 2),       # How far it can shoot.
                    "combat_factor": caps.get("attack", 10),    # How much damage it deals.
                    "vision_range": caps.get("range", 5) + 2    # How far it can see.
                })

            # Give the unit its special skills (components) from the database.
            agent.components = template.get("components", [])

            # Register the unit with the world's Entity Manager.
            self.state.entity_manager.register_entity(agent)
            
            # Record this event for the 'Undo' button.
            if hasattr(self.state, 'undo_stack'):
                from engine.core.undo_system import PlaceEntityCommand
                cmd = PlaceEntityCommand(
                    self.state.map, 
                    self.state.entity_manager, 
                    agent.id, 
                    click_hex, 
                    old_hex=None
                )
                self.state.undo_stack.push(cmd)
            
            # Physically place the unit on the map.
            self.state.map.place_entity(agent.id, click_hex)
            # Update the screen to show our new soldier!
            self.widget.update()
            
            # Cleanup the sidebar menu so it's ready for the next placement.
            self.refresh_roster()

