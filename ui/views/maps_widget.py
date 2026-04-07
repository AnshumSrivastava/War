import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QGridLayout, QFrame, QComboBox)
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
import shutil
from ui.styles.theme import Theme
from engine.state.global_state import GlobalState
import services.map_service as map_service

# --- UI CONFIGURATION ---
# Section Headers
LABEL_MAPS_SECTION = "MAPS & TERRAIN"
LABEL_SCEN_SECTION = "OPERATIONAL MISSIONS"
LABEL_MODEL_SECTION = "INTELLIGENCE VARIANTS"

# Button Labels
LABEL_BTN_DELETE = "DELETE"
LABEL_BTN_NEW = "+ NEW MISSION"
LABEL_BTN_DB = "DATABASE"

# Symbols
SYM_DELETE = "×"

# Dialog & System Messages
TITLE_DELETE_CONFIRM = "TACTICAL DELETION"
MSG_DELETE_CONFIRM_FMT = "Permanently remove this {kind} ({name})?"
MSG_DELETE_SUCCESS_FMT = "<b>DELETED</b> {kind}: {name}"
MSG_DELETE_FAIL_FMT = "Deletion failed: Path not found {path}"
MSG_DELETE_ERR_FMT = "Error during deletion: {error}"
# ------------------------
class ProjectCard(QFrame):
    """A visual card representing a Map or Scenario with a premium tactical aesthetic."""
    clicked = pyqtSignal(dict) 
    double_clicked = pyqtSignal(dict)
    delete_requested = pyqtSignal(dict)
    
    def __init__(self, kind, proj, map_name, root_path, extra="", info=""):
        super().__init__()
        self.kind = kind
        self.proj = proj
        self.map_name = map_name
        self.extra = extra
        
        self.setObjectName("ProjectCard")
        self.setFixedSize(200, 180)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        
        # Thumbnail / Visual Indicator
        self.thumb = QLabel()
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setFixedSize(190, 110)
        self.thumb.setScaledContents(True)
        
        icon_color = Theme.ACCENT_ALLY if kind == "map" else Theme.ACCENT_WARN
        if kind == "simulation": icon_color = Theme.ACCENT_GOOD
        
        bg_color = Theme.BG_DEEP
        
        # --- LOOK FOR REAL THUMBNAIL ---
        thumb_path = os.path.join(root_path, "Projects", proj, "Maps", map_name, "thumbnail.png")
        
        if os.path.exists(thumb_path):
            pix = QPixmap(thumb_path)
            self.thumb.setPixmap(pix.scaled(190, 110, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.thumb.setStyleSheet(f"background-color: {bg_color}; color: {icon_color}; border-radius: 8px;")
            self.thumb.setFont(Theme.get_font(Theme.FONT_HEADER, 14, bold=True))
            self.thumb.setText(kind[0].upper()) # Type Letter (M, S, V)
            
        layout.addWidget(self.thumb)
        
        # Details Area (Tactical Info)
        info_area = QWidget()
        info_layout = QVBoxLayout(info_area)
        info_layout.setContentsMargins(5, 8, 5, 5)
        info_layout.setSpacing(2)
        
        name_lbl = QLabel((extra if extra else map_name).upper())
        name_lbl.setFont(Theme.get_font(Theme.FONT_HEADER, 8, bold=True))
        name_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        
        # Metadata Badge
        meta_layout = QHBoxLayout()
        kind_lbl = QLabel(kind.upper())
        kind_lbl.setStyleSheet(f"color: {icon_color}; font-size: 7px; font-weight: bold; padding: 2px; border: 1px solid {icon_color}; border-radius: 3px;")
        meta_layout.addWidget(kind_lbl)
        meta_layout.addStretch()
        
        info_layout.addWidget(name_lbl)
        info_layout.addLayout(meta_layout)
        layout.addWidget(info_area)
        
        self._setup_style()
        
        # Data Payload
        self.payload = {
            "kind": kind,
            "proj": proj,
            "map_name": map_name,
            "root_path": root_path,
            "extra": extra,
            "info": info
        }
        
        # --- DELETE BUTTON (X) ---
        # Data registries are protected from direct deletion here for safety
        if kind != "data":
            self.btn_del = QPushButton(SYM_DELETE, self)
            self.btn_del.setFixedSize(24, 24)
            self.btn_del.move(170, 5)
            self.btn_del.setCursor(Qt.PointingHandCursor)
            self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.payload))
            self.btn_del.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Theme.TEXT_DIM};
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background: {Theme.ACCENT_ENEMY};
                    color: white;
                }}
            """)
            self.btn_del.show()

    def _setup_style(self):
        self.setProperty("selected", "false")
        self.setStyleSheet(f"""
            QFrame#ProjectCard {{
                background-color: {Theme.BG_SURFACE};
                border-radius: 10px;
                border: 1px solid {Theme.BORDER_STRONG};
            }}
            QFrame#ProjectCard[selected="true"] {{
                background-color: {Theme.BG_INPUT};
                border: 2px solid {Theme.ACCENT_ALLY};
            }}
            QFrame#ProjectCard:hover {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.TEXT_DIM};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.payload)
            
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.payload)

class MapsWidget(QWidget):
    """
    Project Dashboard: Tactical interface for the current project.
    """
    deep_link_requested = pyqtSignal(dict) 
    
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.mw = parent
        self.maps = {} 
        self.scenarios = {} 
        self.models = {} 
        self.registries = {} 
        
        self.active_map = None
        self.active_scen = None
        self.active_model = None
        self.active_reg = None
        
        self.state = state if state else GlobalState()
        
        # --- MAIN LAYOUT (Full Width) ---
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(25)
        
        # --- HEADER (Project Selection) ---
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        from PyQt5.QtWidgets import QComboBox
        self.project_combo = QComboBox()
        self.project_combo.setFixedSize(250, 45)
        self.project_combo.setFont(Theme.get_font(Theme.FONT_HEADER, 14, bold=True))
        self.project_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_SURFACE};
                color: {Theme.ACCENT_ALLY};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 6px;
                padding-left: 10px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        h_layout.addWidget(self.project_combo)
        
        btn_delete = QPushButton(LABEL_BTN_DELETE)
        btn_delete.setFixedSize(80, 45)
        btn_delete.setStyleSheet(f"background-color: {Theme.BG_DEEP}; border: 1px solid {Theme.ACCENT_ENEMY}; color: {Theme.ACCENT_ENEMY}; font-weight: bold; font-size: 10px;")
        btn_delete.clicked.connect(lambda: self.mw.action_delete_project(self.project_combo.currentText()) if self.mw else None)
        h_layout.addWidget(btn_delete)
        
        h_layout.addStretch()
        
        btn_create = QPushButton(LABEL_BTN_NEW)
        btn_create.setFixedSize(140, 40)
        btn_create.setStyleSheet(f"background-color: {Theme.BG_DEEP}; border: 1px solid {Theme.ACCENT_ALLY}; color: {Theme.ACCENT_ALLY}; font-weight: bold;")
        btn_create.clicked.connect(self.mw.action_save_scenario if self.mw else lambda: None)
        h_layout.addWidget(btn_create)
        
        btn_database = QPushButton(LABEL_BTN_DB)
        btn_database.setFixedSize(140, 40)
        btn_database.setStyleSheet(f"background-color: {Theme.BG_DEEP}; border: 1px solid {Theme.ACCENT_GOOD}; color: {Theme.ACCENT_GOOD}; font-weight: bold;")
        btn_database.clicked.connect(lambda: self.mw.switch_mode(8) if self.mw else None)
        h_layout.addWidget(btn_database)
        
        self.layout.addWidget(header)
        
        # --- GRIDS (Scrollable) ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.grid_container = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(40)
        
        # Sections
        self.maps_grid = self._setup_section(LABEL_MAPS_SECTION)
        self.scen_grid = self._setup_section(LABEL_SCEN_SECTION, color=Theme.ACCENT_WARN)
        self.model_grid = self._setup_section(LABEL_MODEL_SECTION, color=Theme.ACCENT_GOOD)
        
        self.scroll.setWidget(self.grid_container)
        self.layout.addWidget(self.scroll, 1)
        
        self.refresh_list()

    def _setup_section(self, title, color=Theme.TEXT_DIM):
        group = QFrame()
        l = QVBoxLayout(group)
        l.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {color}; border-bottom: 2px solid {color if color != Theme.TEXT_DIM else Theme.BORDER_STRONG}; padding-bottom: 8px; margin-bottom: 15px; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        l.addWidget(lbl)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        l.addLayout(grid)
        self.grid_layout.addWidget(group)
        return grid

    def _on_project_changed(self, text):
        if text and text != self.state.current_project:
            self.state.current_project = text
            self.active_map = None
            self.active_scen = None
            self.refresh_list()

    def refresh_list(self, map_changed=True):
        """Populates the HQ with Projects, Maps, and Missions."""
        if self.mw and hasattr(self.mw, 'data_loader'):
            proj_folder = os.path.join(self.mw.data_loader.content_root, "Projects")
            projects = sorted([d for d in os.listdir(proj_folder) if os.path.isdir(os.path.join(proj_folder, d))]) if os.path.exists(proj_folder) else ["Default"]
            
            self.project_combo.blockSignals(True)
            if self.project_combo.count() == 0 or sorted([self.project_combo.itemText(i) for i in range(self.project_combo.count())]) != projects:
                self.project_combo.clear()
                self.project_combo.addItems(projects)
            self.project_combo.setCurrentText(self.state.current_project or "Default")
            self.project_combo.blockSignals(False)

        proj_name = self.state.current_project or "Default"
        result = map_service.get_project_manifest(proj_name)
        if not result.ok: return
            
        manifest = result.data
        root_path = manifest["root_path"]
        maps_dict = manifest["maps"]

        # 1. RENDER MAPS
        self._clear_grid(self.maps_grid, self.maps)
        col, row = 0, 0
        for m_name, m_info in sorted(maps_dict.items()):
            card = ProjectCard("map", proj_name, m_name, root_path)
            card.clicked.connect(self._on_item_clicked)
            card.double_clicked.connect(self._on_item_double_clicked)
            card.delete_requested.connect(self._on_item_delete_requested)
            self.maps[m_name] = card
            self.maps_grid.addWidget(card, row, col)
            col += 1
            if col > 4: col = 0; row += 1 # Increased columns for wider view

        # 2. RENDER MISSIONS (Scenarios) — show all scenarios from all maps
        self._clear_grid(self.scen_grid, self.scenarios)
        col, row = 0, 0
        for m_name, m_info in sorted(maps_dict.items()):
            for s_name in m_info.get("scenarios", []):
                card_label = f"{s_name}"
                card_info  = f"Map: {m_name}"
                card = ProjectCard("scenario", proj_name, m_name, root_path,
                                   extra=s_name, info=card_info)
                card.clicked.connect(self._on_item_clicked)
                card.double_clicked.connect(self._on_item_double_clicked)
                card.delete_requested.connect(self._on_item_delete_requested)
                # Use a unique key: map/scenario so duplicate names across maps don't collide
                key = f"{m_name}/{s_name}"
                self.scenarios[key] = card
                self.scen_grid.addWidget(card, row, col)
                col += 1
                if col > 4: col = 0; row += 1


        # 3. RENDER VARIANTS (Models) — show all simulations from all maps
        self._clear_grid(self.model_grid, self.models)
        col, row = 0, 0
        for m_name, m_info in sorted(maps_dict.items()):
            for mo_name in m_info.get("simulations", []):
                card = ProjectCard("simulation", proj_name, m_name, root_path,
                                   extra=mo_name, info=f"Map: {m_name}")
                card.double_clicked.connect(self._on_item_double_clicked)
                card.delete_requested.connect(self._on_item_delete_requested)
                self.models[f"{m_name}/{mo_name}"] = card
                self.model_grid.addWidget(card, row, col)
                col += 1
                if col > 4: col = 0; row += 1
        
        self._update_selection_borders()

    def _update_selection_borders(self):
        for name, card in {**self.maps, **self.scenarios, **self.models, **self.registries}.items():
            is_sel = (name == self.active_map or name == self.active_scen or name == self.active_model or name == self.active_reg)
            card.setProperty("selected", "true" if is_sel else "false")
            card.style().unpolish(card)
            card.style().polish(card)

    def _on_item_clicked(self, payload):
        if payload["kind"] == "map":
            self.active_map = payload["map_name"]
            self.active_scen = None
            self.active_reg = None
            self.refresh_list(map_changed=False)
        elif payload["kind"] == "data":
            self.active_reg = payload["extra"]
        else:
            self.active_scen = payload["extra"]
            self.active_reg = None
        
        self._update_selection_borders()

    def _on_item_double_clicked(self, payload):
        self._launch_active(payload)

    def _on_item_delete_requested(self, payload):
        """Removes the target Map, Scenario, or Simulation from disk."""
        kind = payload["kind"]
        proj = payload["proj"]
        map_name = payload["map_name"]
        extra = payload.get("extra", "")
        
        # 1. CONFIRMATION
        from ui.components.themed_widgets import ThemedMessageBox
        confirm = ThemedMessageBox.question(self, TITLE_DELETE_CONFIRM, 
                                            MSG_DELETE_CONFIRM_FMT.format(kind=kind.upper(), name=extra if extra else map_name))
        if not confirm:
            return
            
        # 2. RESOLVE PATH
        target_path = ""
        root = payload["root_path"]
        
        if kind == "map":
             # Entire map folder
             target_path = os.path.join(root, "Projects", proj, "Maps", map_name)
        elif kind == "scenario":
             # Specific Scenario JSON
             target_path = os.path.join(root, "Projects", proj, "Maps", map_name, "Scenarios", f"{extra}.json")
        elif kind == "simulation":
             # Specific Simulation JSON
             target_path = os.path.join(root, "Projects", proj, "Maps", map_name, "Simulations", f"{extra}.json")
             
        # 3. EXECUTE
        try:
            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
                    
                self.mw.log_info(MSG_DELETE_SUCCESS_FMT.format(kind=kind.upper(), name=extra or map_name))
                
                # Update current state if we deleted the active item
                if self.active_map == map_name and kind == "map":
                     self.active_map = None
                if self.active_scen == extra and kind == "scenario":
                     self.active_scen = None
                
                self.refresh_list()
            else:
                self.mw.log_error(MSG_DELETE_FAIL_FMT.format(path=target_path))
        except Exception as e:
            self.mw.log_error(MSG_DELETE_ERR_FMT.format(error=str(e)))

    def _launch_active(self, payload):
        load_type = payload["kind"]
        print(f"DEBUG: Initiating HQ launch for {load_type}: {payload.get('extra', payload['map_name'])}")
        
        data = {
            "type": load_type,
            "project": payload["proj"],
            "map_name": payload["map_name"],
            "root": payload["root_path"],
            "extra": payload.get("extra", "")
        }
        if load_type == "scenario": data["scenario_name"] = payload["extra"]
        if load_type == "simulation": data["model_name"] = payload["extra"]
        
        self.deep_link_requested.emit(data)

    def _clear_grid(self, grid, cache):
        while grid and grid.count():
            item = grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        cache.clear()


