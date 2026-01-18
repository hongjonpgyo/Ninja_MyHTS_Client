from PyQt6.QtWidgets import QTableWidgetItem, QAbstractItemView, QHeaderView, QMenu
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

class WatchlistController:
    def __init__(self, table, on_add_fav, on_remove_fav, favorites: set[str]):
        self.table = table
        self.on_add_fav = on_add_fav
        self.on_remove_fav = on_remove_fav
        self.row_map = {}          # symbol_code -> row index
        self.prev_price = {}       # symbol_code -> last price
        self.favorites = favorites

        self.bold_font = QFont()
        self.bold_font.setBold(True)

        self._setup_table()

    # -------------------------------------------------
    def _setup_table(self):
        t = self.table
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(
            ["종목명", "코드", "현재가", "전일대비"]
        )

        t.verticalHeader().setVisible(False)
        t.verticalHeader().setDefaultSectionSize(28)
        t.horizontalHeader().setFixedHeight(26)

        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        t.setShowGrid(False)

        header = t.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 🎨 스타일 통일
        t.setStyleSheet("""
        QTableWidget {
            background-color: #1f1f1f;
            color: #e0e0e0;
            font-size: 12px;
        }
        QHeaderView::section {
            background-color: #2b2b2b;
            color: #cccccc;
            font-size: 11px;
            padding: 6px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: #0a46c7;
            color: white;
        }
        """)

        t.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        t.customContextMenuRequested.connect(self._on_context_menu)

    # -------------------------------------------------
    def load_default(self):
        rows = [
            ("코스피 선물", "101WC000", 469.40, +2.35),
            ("S&P 500", "ESZ25", 6658.75, -0.10),
            ("미니항셍", "HMHU25", 26105, +1.20),
            ("유로화", "UROZ25", 1.17220, -0.04),
            ("나스닥100", "NQZ25", 24590.75, +0.18),
            ("금선물", "GCZ25", 3777.5, -0.16),
        ]

        self.table.setRowCount(len(rows))

        for r, (name, code, price, diff) in enumerate(rows):
            self.row_map[code] = r
            self.prev_price[code] = price

            self.table.setItem(r, 0, self._item(name, "#ffffff"))
            self.table.setItem(r, 1, self._item(code, "#aaaaaa"))
            self.table.setItem(
                r, 2,
                self._price_item(price)
            )

            arrow, color = self._diff_style(diff)
            self.table.setItem(
                r, 3,
                self._item(f"{arrow} {diff:+.2f}".strip(), color, Qt.AlignmentFlag.AlignRight)
            )

    # -------------------------------------------------
    def update_price(self, code: str, last_price: float):
        if code not in self.row_map:
            return

        row = self.row_map[code]
        prev = self.prev_price.get(code, last_price)
        diff = last_price - prev

        price_item = self.table.item(row, 2)
        diff_item = self.table.item(row, 3)

        # -------------------------
        # 현재가
        # -------------------------
        if price_item:
            price_item.setText(f"{last_price:,.2f}")

            if diff > 0:
                fg = QColor("#2ecc71")
                bg = QColor(46, 204, 113, 40)
            elif diff < 0:
                fg = QColor("#e74c3c")
                bg = QColor(231, 76, 60, 40)
            else:
                fg = QColor("#FFD700")
                bg = QColor("#1f1f1f")

            price_item.setForeground(fg)
            price_item.setBackground(bg)

            # 잠깐 하이라이트 → 원복
            QTimer.singleShot(200, lambda r=row: self._clear_price_bg(r))

        # -------------------------
        # 전일대비
        # -------------------------
        if diff_item:
            arrow, color = self._diff_style(diff)
            diff_item.setText(f"{arrow} {diff:+.2f}".strip())
            diff_item.setForeground(QColor(color))

        self.prev_price[code] = last_price

    # -------------------------------------------------
    def _clear_price_bg(self, row):
        item = self.table.item(row, 2)
        if item:
            item.setBackground(QColor("#1f1f1f"))

    # -------------------------------------------------
    # helpers
    # -------------------------------------------------
    def _item(self, text, color, align=None):
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        if align:
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def _price_item(self, price):
        item = QTableWidgetItem(f"{price:,.2f}")
        item.setFont(self.bold_font)
        item.setForeground(QColor("#FFD700"))
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _diff_style(self, diff):
        if diff > 0:
            return "▲", "#2ecc71"
        elif diff < 0:
            return "▼", "#e74c3c"
        return "", "#aaaaaa"

    def _on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        code_item = self.table.item(row, 1)  # 코드 컬럼
        name_item = self.table.item(row, 0)

        if not code_item or not name_item:
            return

        code = code_item.text()
        name = name_item.text().replace("★ ", "")

        menu = QMenu(self.table)

        if code not in self.favorites:
            act_add = menu.addAction("⭐ 즐겨찾기 추가")
            act_add.triggered.connect(
                lambda: self._add_favorite(row, code, name)
            )
        else:
            act_remove = menu.addAction("❌ 즐겨찾기 제거")
            act_remove.triggered.connect(
                lambda: self._remove_favorite(row, code)
            )

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _add_favorite(self, row, code, name):
        self.on_add_fav(code)  # 🔥 MainWindow로 위임

        item = self.table.item(row, 0)
        item.setText(f"★ {name}")
        item.setForeground(QColor("#FFD700"))

    def _remove_favorite(self, row, code):
        self.on_remove_fav(code)

        item = self.table.item(row, 0)
        item.setText(item.text().replace("★ ", ""))
        item.setForeground(QColor("#e0e0e0"))

    def mark_favorite(self, code: str):
        if code not in self.row_map:
            return

        row = self.row_map[code]
        item = self.table.item(row, 0)

        if not item:
            return

        name = item.text().replace("★ ", "")
        item.setText(f"★ {name}")
        item.setForeground(QColor("#FFD700"))

    def unmark_favorite(self, code: str):
        if code not in self.row_map:
            return

        row = self.row_map[code]
        item = self.table.item(row, 0)

        if not item:
            return

        item.setText(item.text().replace("★ ", ""))
        item.setForeground(QColor("#e0e0e0"))




