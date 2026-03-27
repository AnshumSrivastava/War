import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QGridLayout, QFrame)
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from ui.styles.theme import Theme
import services.map_service as map_service

class ProjectCard(QFrame):
    """A visual card representing a Map or Scenario."""
    clicked = pyqtSignal(dict) # Data payload
    double_clicked = pyqtSignal(dict)
    
    def __init__(self, kind, proj, map_name, root_path, extra="", info=""):
        super().__init__()
        self.kind = kind
        self.proj = proj
        self.map_name = map_name
        self.extra = extra
        
        self.setObjectName("ProjectCard")
        self.setFixedSize(220, 160)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Thumbnail / Icon Area
        self.thumb = QLabel()
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setFixedSize(220, 100)
        self.thumb.setScaledContents(True) # Ensure pixmap fits
        
        icon_color = Theme.ACCENT_ALLY if kind == "map" else Theme.ACCENT_WARN
        bg_color = Theme.BG_INPUT
        
        # --- LOOK FOR REAL THUMBNAIL ---
        thumb_path = os.path.join(root_path, "Projects", proj, "Maps", map_name, "thumbnail.png")
        
        if os.path.exists(thumb_path):
            pix = QPixmap(thumb_path)
            self.thumb.setPixmap(pix.scaled(220, 100, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.thumb.setStyleSheet(f"background-color: {bg_color}; border-bottom: 1px solid {Theme.BORDER_STRONG};")
        else:
            self.thumb.setStyleSheet(f"background-color: {bg_color}; border-bottom: 1px solid {Theme.BORDER_STRONG}; color: {icon_color};")
            self.thumb.setFont(Theme.get_font(Theme.FONT_HEADER, 12, bold=True))
            self.thumb.setText(kind.upper())
        
        layout.addWidget(self.thumb)
        
        # Details Footer
        footer = QWidget()
        footer.setObjectName("CardFooter")
        footer.setStyleSheet(f"background-color: {Theme.BG_SURFACE};")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        footer_layout.setSpacing(2)
        
        name_lbl = QLabel((extra if extra else map_name).upper())
        name_lbl.setFont(Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        name_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        
        type_lbl = QLabel(f"{kind} | {info}" if info else kind)
        type_lbl.setFont(Theme.get_font(Theme.FONT_BODY, 8))
        type_lbl.setStyleSheet(f"color: {Theme.TEXT_DIM};")
        
        footer_layout.addWidget(name_lbl)
        footer_layout.addWidget(type_lbl)
        layout.addWidget(footer)
        
        self._setup_style()
        
        # Data Payload
        self.payload = {
            "kind": kind,
            "proj": proj,
            "map_name": map_name,
            "root_path": root_path,
            "extra": extra
        }

    def _setup_style(self):
        self.setProperty("selected", "false")
        self.setStyleSheet(f"""
            QFrame#ProjectCard {{
                background-color: {Theme.BG_SURFACE};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER_STRONG};
            }}
            QFrame#ProjectCard[selected="true"] {{
                border: 2px solid {Theme.ACCENT_ALLY if self.kind == "map" else Theme.ACCENT_WARN};
            }}
            QFrame#ProjectCard:hover {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.ACCENT_ALLY if self.kind == "map" else Theme.ACCENT_WARN};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # print(f"DEBUG: ProjectCard '{self.map_name}' clicked.")
            self.clicked.emit(self.payload)
            
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            print(f"DEBUG: ProjectCard '{self.map_name}' DOUBLE-CLICKED (kind={self.kind}).")
            self.double_clicked.emit(self.payload)

class MapsWidget(QWidget):
    """
    Project Dashboard: Visual thumbnail-based interface for the current project.
    """
    deep_link_requested = pyqtSignal(dict) # Changed to dict
    
    def __init__(self, parent=None, state=None):
        super().__init__(parent)
        self.mw = parent
        self.maps = {} # Name -> Card
        self.scenarios = {} # Name -> Card
        self.models = {} # Name -> Card
        
        self.active_map = None
        self.active_scen = None
        
        self.state = state if state else GlobalState()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # --- HEADER ---
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("PROJECT: UNKNOWN")
        self.title_label.setFont(Theme.get_font(Theme.FONT_HEADER, 18, bold=True))
        self.title_label.setStyleSheet(f"color: {Theme.ACCENT_ALLY};")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Actions
        self.btn_new_map = QPushButton("NEW MAP")
        self.btn_new_map.setFixedSize(120, 40)
        self.btn_new_map.clicked.connect(self.mw.action_create_new_map if self.mw else lambda: None)
        header_layout.addWidget(self.btn_new_map)
        
        self.btn_new_scen = QPushButton("NEW SCENARIO")
        self.btn_new_scen.setFixedSize(140, 40)
        self.btn_new_scen.clicked.connect(self.mw.action_save_scenario if self.mw else lambda: None)
        header_layout.addWidget(self.btn_new_scen)
        
        self.layout.addWidget(header_container)
        
        # --- SCROLL AREA FOR CARDS ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.container = QWidget()
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(30)
        
        # 1. MAPS SECTION
        self.maps_section = self._create_section("MAPS (TERRAIN)")
        self.maps_grid = QGridLayout()
        self.maps_grid.setSpacing(20)
        self.maps_grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.maps_section.layout().addLayout(self.maps_grid)
        self.content_layout.addWidget(self.maps_section)
        
        # 2. SCENARIOS SECTION
        self.scen_section = self._create_section("TACTICAL MISSIONS", Theme.ACCENT_WARN)
        self.scen_grid = QGridLayout()
        self.scen_grid.setSpacing(20)
        self.scen_grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.scen_section.layout().addLayout(self.scen_grid)
        self.content_layout.addWidget(self.scen_section)
        
        # 3. MODELS SECTION
        self.model_section = self._create_section("LEARNED VARIANTS (MODELS)", Theme.ACCENT_GOOD)
        self.model_grid = QGridLayout()
        self.model_grid.setSpacing(20)
        self.model_grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.model_section.layout().addLayout(self.model_grid)
        self.content_layout.addWidget(self.model_section)
        
        self.content_layout.addStretch()
        
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        
        self.refresh_list()

    def _create_section(self, title, color=Theme.TEXT_DIM):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(title)
        lbl.setFont(Theme.get_font(Theme.FONT_HEADER, 11, bold=True))
        lbl.setStyleSheet(f"color: {color}; border-bottom: 2px solid {color if color != Theme.TEXT_DIM else Theme.BORDER_STRONG}; padding-bottom: 5px; margin-bottom: 10px;")
        layout.addWidget(lbl)
        return frame

    def refresh_list(self, map_changed=True, scen_changed=True):
        """Populates the dashboard with Maps, Missions, and Learned Models."""
        proj_name = self.state.current_project or "Default"
        self.title_label.setText(f"PROJECT: {proj_name.upper()}")
        
        result = map_service.get_project_manifest(proj_name)
        if not result.ok:
            self.title_label.setText(f"PROJECT: {proj_name.upper()} (ERROR: {result.message})")
            return
            
        manifest = result.data
        root_path = manifest["root_path"]
        maps_dict = manifest["maps"]
        
        # 1. RENDER MAPS (Global)
        if map_changed:
            self._clear_grid(self.maps_grid, self.maps)
            m_row, m_col = 0, 0
            for m_name, m_info in sorted(maps_dict.items()):
                m_card = ProjectCard("map", proj_name, m_name, root_path, info="Terrain")
                m_card.clicked.connect(self._on_map_selected)
                m_card.double_clicked.connect(self._on_map_load_requested)
                self.maps[m_name] = m_card
                self.maps_grid.addWidget(m_card, m_row, m_col)
                m_col += 1
                if m_col > 3: m_col = 0; m_row += 1

        # 2. RENDER MISSIONS (Filtered by Active Map)
        if scen_changed:
            self._clear_grid(self.scen_grid, self.scenarios)
            if self.active_map and self.active_map in maps_dict:
                s_row, s_col = 0, 0
                for s_name in maps_dict[self.active_map].get("scenarios", []):
                    s_card = ProjectCard("scenario", proj_name, self.active_map, root_path, extra=s_name, info=f"Map: {self.active_map}")
                    s_card.clicked.connect(self._on_scenario_selected)
                    s_card.double_clicked.connect(self._on_scenario_load_requested)
                    self.scenarios[s_name] = s_card
                    self.scen_grid.addWidget(s_card, s_row, s_col)
                    s_col += 1
                    if s_col > 4: s_col = 0; s_row += 1

        # 3. RENDER MODELS (Filtered by Map and Scenario)
        self._clear_grid(self.model_grid, self.models)
        if self.active_map and self.active_map in maps_dict:
            mo_row, mo_col = 0, 0
            for mo_name in maps_dict[self.active_map].get("simulations", []):
                # Filter models to containing scenario name if selected
                if not self.active_scen or self.active_scen in mo_name:
                    mo_card = ProjectCard("simulation", proj_name, self.active_map, root_path, extra=mo_name, info=f"Model: {mo_name}")
                    mo_card.double_clicked.connect(self._on_simulation_load_requested)
                    self.models[mo_name] = mo_card
                    self.model_grid.addWidget(mo_card, mo_row, mo_col)
                    mo_col += 1
                    if mo_col > 4: mo_col = 0; mo_row += 1
        
        self._update_selection_borders()

    def _update_selection_borders(self):
        """Visually marks selected items using dynamic properties."""
        from PyQt5.QtWidgets import QStyle
        # Maps
        for name, card in self.maps.items():
            val = "true" if name == self.active_map else "false"
            card.setProperty("selected", val)
            card.style().unpolish(card)
            card.style().polish(card)
        
        # Scenarios
        for name, card in self.scenarios.items():
            val = "true" if name == self.active_scen else "false"
            card.setProperty("selected", val)
            card.style().unpolish(card)
            card.style().polish(card)

    def _on_map_selected(self, payload):
        if self.active_map == payload["map_name"]: return
        self.active_map = payload["map_name"]
        self.active_scen = None
        self.refresh_list(map_changed=False, scen_changed=True)

    def _on_scenario_selected(self, payload):
        if self.active_scen == payload["extra"]: return
        self.active_scen = payload["extra"]
        self.refresh_list(map_changed=False, scen_changed=False) # Models only

    def _on_map_load_requested(self, payload):
        print(f"DEBUG: MapsWidget: Map load requested for '{payload['map_name']}'")
        self.deep_link_requested.emit({
            "type": "map",
            "project": payload["proj"],
            "map_name": payload["map_name"],
            "root": payload["root_path"]
        })

    def _on_scenario_load_requested(self, payload):
        print(f"DEBUG: MapsWidget: Scenario load requested for '{payload['extra']}'")
        self.deep_link_requested.emit({
            "type": "scenario",
            "project": payload["proj"],
            "map_name": payload["map_name"],
            "scenario_name": payload["extra"],
            "root": payload["root_path"]
        })

    def _on_simulation_load_requested(self, payload):
        print(f"DEBUG: MapsWidget: Simulation load requested for '{payload['extra']}'")
        self.deep_link_requested.emit({
            "type": "simulation",
            "project": payload["proj"],
            "map_name": payload["map_name"],
            "model_name": payload["extra"],
            "root": payload["root_path"]
        })

    def _clear_grid(self, grid, cache):
        if not grid: return
        while grid.count():
            item = grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        cache.clear()
