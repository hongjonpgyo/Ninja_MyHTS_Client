from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QTableWidgetItem, QAbstractItemView, QHeaderView
from ui.utils.formatter import fmt_time


class OpenOrdersWidget(QtWidgets.QWidget):
    def __init__(self, main_window, order_api, account_id):
        super().__init__()

        self.main = main_window      # 🔥 핵심
        self.order_api = order_api
        self.account_id = account_id

        self.resize(900, 420)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # =================================================
        # 🔹 SUMMARY STRIP (제목형)
        # =================================================
        self.summaryBar = QtWidgets.QWidget()
        self.summaryBar.setFixedHeight(44)
        self.summaryBar.setStyleSheet("""
        QWidget {
            background-color: #262626;
            border-radius: 6px;
        }
        """)

        self.lblTitle = QtWidgets.QLabel("미체결 주문건수")
        self.lblTitle.setStyleSheet("color:#ffffff; font-size:13px; font-weight:600;")

        self.lblTotal = QtWidgets.QLabel("0")
        self.lblTotal.setStyleSheet("color:#f1c40f; font-size:18px; font-weight:700;")

        self.lblSymbols = QtWidgets.QLabel("")
        self.lblSymbols.setStyleSheet("color:#aaaaaa; font-size:11px;")

        title_layout = QtWidgets.QVBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.lblTitle)
        title_layout.addWidget(self.lblSymbols)

        summary_layout = QtWidgets.QHBoxLayout(self.summaryBar)
        summary_layout.setContentsMargins(12, 6, 12, 6)
        summary_layout.addLayout(title_layout)
        summary_layout.addStretch()
        summary_layout.addWidget(self.lblTotal)

        root.addWidget(self.summaryBar)

        # =================================================
        # 🔹 MAIN AREA (Table + Guide Panel)
        # =================================================
        main = QtWidgets.QHBoxLayout()
        main.setSpacing(8)

        # -------------------------
        # Table
        # -------------------------
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["종목", "구분", "주문가", "수량", "시간", "주문번호", "상태"]
        )

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 중요 컬럼만 비율 조정
        header.setStretchLastSection(False)
        header.resizeSection(0, 120)  # Symbol
        header.resizeSection(1, 80)  # Side
        header.resizeSection(2, 120)  # Price
        header.resizeSection(3, 70)  # Qty
        header.resizeSection(4, 120)  # Time
        header.resizeSection(5, 90)  # OrderID
        header.resizeSection(6, 90)  # Status


        self.table.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.table.setStyleSheet("""
        QTableWidget {
            background-color: #1e1e1e;
            border: none;
        }
        QTableWidget::item {
            padding: 6px;
        }
        QTableWidget::item:hover {
            background-color: #2a2a2a;
        }
        QTableWidget::item:selected {
            background-color: #1f4f99;
        }
        QHeaderView::section {
            background-color: #2b2b2b;
            color: white;
            padding: 6px;
            border: none;
        }
        """)

        main.addWidget(self.table, 1)

        # -------------------------
        # Guide Panel (오른쪽)
        # -------------------------
        guide = QtWidgets.QWidget()
        guide.setFixedWidth(180)
        guide.setStyleSheet("""
        QWidget {
            background-color: #232323;
            border-radius: 6px;
        }
        """)

        guide_layout = QtWidgets.QVBoxLayout(guide)
        guide_layout.setContentsMargins(10, 10, 10, 10)
        guide_layout.setSpacing(10)

        lblGuideTitle = QtWidgets.QLabel("Open Orders Guide")
        lblGuideTitle.setStyleSheet("color:#ffffff; font-size:12px; font-weight:600;")

        lblGuideText = QtWidgets.QLabel(
            "• 더블클릭 → 주문 패널 연동\n"
            "• 다중 선택 → 일괄 취소\n"
            "• 현재 심볼 주문 강조"
        )
        lblGuideText.setStyleSheet("color:#aaaaaa; font-size:11px;")
        lblGuideText.setWordWrap(True)

        guide_layout.addWidget(lblGuideTitle)
        guide_layout.addWidget(lblGuideText)
        guide_layout.addStretch()

        main.addWidget(guide)

        root.addLayout(main)

        # =================================================
        # 🔹 BUTTONS
        # =================================================
        btns = QtWidgets.QHBoxLayout()
        btns.addStretch()

        self.btnCancel = QtWidgets.QPushButton("선택 주문 취소")
        # self.btnRefresh = QtWidgets.QPushButton("새로고침")

        self.btnCancel.setFixedWidth(160)
        # self.btnRefresh.setFixedWidth(120)

        self.btnCancel.setStyleSheet("""
        QPushButton {
            background-color: #803333;
            color: white;
            padding: 8px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #a94444;
        }
        """)

        # self.btnRefresh.setStyleSheet("""
        # QPushButton {
        #     background-color: #444444;
        #     color: white;
        #     padding: 8px;
        #     border-radius: 6px;
        # }
        # QPushButton:hover {
        #     background-color: #555555;
        # }
        # """)

        btns.addWidget(self.btnCancel)
        # btns.addWidget(self.btnRefresh)
        root.addLayout(btns)

        # =================================================
        # Signals / Timer
        # =================================================
        # self.btnRefresh.clicked.connect(self.refresh)
        self.btnCancel.clicked.connect(self.cancel_selected_orders)

        # self.timer = QtCore.QTimer(self)
        # # self.timer.timeout.connect(self.refresh)
        # self.timer.start(1000)

        # self.refresh()

    # -------------------------------------------------
    # def refresh(self):
    #     try:
    #         orders = self.order_api.get_open_orders(self.account_id)
    #         if isinstance(orders, list):
    #             self._update_summary(orders)
    #             self.update_table(orders)
    #     except Exception as e:
    #         print("[OpenOrdersWidget] refresh error:", e)

    # -------------------------------------------------
    def _update_summary(self, orders):
        total = len(orders)
        self.lblTotal.setText(str(total))

        sym_cnt = {}
        for o in orders:
            sym = o.get("symbol", "")
            sym_cnt[sym] = sym_cnt.get(sym, 0) + 1

        self.lblSymbols.setText(
            "   ".join(f"{k} {v}" for k, v in sym_cnt.items())
        )

    # -------------------------------------------------
    def _set_item(self, r, c, v, *, fg="#e0e0e0", align=QtCore.Qt.AlignmentFlag.AlignCenter, bold=False):
        item = QTableWidgetItem("" if v is None else str(v))
        item.setTextAlignment(align | QtCore.Qt.AlignmentFlag.AlignVCenter)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        item.setForeground(QtGui.QColor(fg))

        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)

        self.table.setItem(r, c, item)
        return item

    # -------------------------------------------------
    def update_table(self, orders):
        self._update_summary(orders)
        self.table.setRowCount(len(orders))

        current_symbol = getattr(self, "current_symbol", None)

        for r, o in enumerate(orders):
            symbol = o.get("symbol", "")
            side = str(o.get("side", "")).upper()
            price = o.get("price", "")
            qty = o.get("qty", "")
            time = fmt_time(o.get("created_at"))
            oid = o.get("order_id", "")
            status = o.get("status", "OPEN")

            self._set_item(r, 0, symbol)
            side_item = self._set_item(r, 1, side)
            price_item = self._set_item(r, 2, price)
            self._set_item(r, 3, qty)
            self._set_item(r, 4, time)
            self._set_item(r, 5, oid)
            st = self._set_item(r, 6, f" {status} ")

            # BUY / SELL 컬러
            side_color = QtGui.QColor("#2ecc71" if side == "BUY" else "#e74c3c")
            side_item.setForeground(side_color)
            price_item.setForeground(QtGui.QColor("#f1c40f"))

            # ✅ 현재 심볼 강조
            if current_symbol and symbol == current_symbol:
                for c in range(self.table.columnCount()):
                    it = self.table.item(r, c)
                    if it:
                        it.setBackground(QtGui.QColor(0, 120, 215, 60))

    # -------------------------------------------------
    def cancel_selected_orders(self):
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            QtWidgets.QMessageBox.warning(self, "알림", "선택된 주문이 없습니다.")
            return

        order_ids = [int(self.table.item(r, 5).text()) for r in rows]

        # 🔥 async 작업으로 넘김
        self.main.enqueue_async(
            self._cancel_orders_async(order_ids)
        )

    async def _cancel_orders_async(self, order_ids):
        try:
            res = await self.order_api.cancel_orders(order_ids)

            if res.get("ok"):
                self.main.safe_ui(
                    QtWidgets.QMessageBox.information,
                    self, "완료", "주문 취소 완료"
                )
            else:
                self.main.safe_ui(
                    QtWidgets.QMessageBox.warning,
                    self, "오류", str(res)
                )

            # 🔄 미체결 다시 조회
            await self.main.fetch_open_orders()

        except Exception as e:
            print("[cancel_selected_orders ERROR]", e)


