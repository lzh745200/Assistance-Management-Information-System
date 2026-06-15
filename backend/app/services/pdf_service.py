import io
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from sqlalchemy.orm import Session
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PDFReportService:
    """PDF报表生成服务"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        """初始化自定义样式"""
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Title"],
                fontSize=18,
                spaceAfter=20,
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=12,
                textColor=colors.HexColor("#4472C4"),
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Normal_CN",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Footer",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.gray,
            )
        )

    def generate_users_report(self, users: List[Dict]) -> bytes:
        """生成用户报表PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        elements = []

        title = Paragraph("用户列表报表", self.styles["ReportTitle"])
        elements.append(title)

        subtitle = Paragraph(
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>" f"用户总数：{len(users)}",
            self.styles["Normal_CN"],
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 20))

        headers = ["ID", "用户名", "邮箱", "姓名", "角色", "状态"]
        data = [[h for h in headers]]

        for u in users:
            row = [
                str(u.get("id", "")),
                u.get("username", ""),
                u.get("email", "") or "-",
                u.get("full_name", "") or "-",
                u.get("role", "") or "-",
                "启用" if u.get("is_active") else "禁用",
            ]
            data.append(row)

        table = Table(
            data,
            colWidths=[
                0.5 * inch,
                1.2 * inch,
                1.5 * inch,
                1 * inch,
                0.8 * inch,
                0.8 * inch,
            ],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 30))

        footer = Paragraph(
            f"页脚 - 帮扶管理信息系统 - {datetime.now().year}",
            self.styles["Footer"],
        )
        elements.append(footer)

        doc.build(elements)
        return buffer.getvalue()

    def generate_villages_report(self, villages: List[Dict]) -> bytes:
        """生成村庄报表PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        elements = []

        title = Paragraph("村庄列表报表", self.styles["ReportTitle"])
        elements.append(title)

        subtitle = Paragraph(
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>" f"村庄总数：{len(villages)}",
            self.styles["Normal_CN"],
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 20))

        headers = ["ID", "名称", "编码", "省份", "城市", "人口", "状态"]
        data = [[h for h in headers]]

        for v in villages:
            row = [
                str(v.get("id", "")),
                v.get("name", ""),
                v.get("code", ""),
                v.get("province", "") or "-",
                v.get("city", "") or "-",
                str(v.get("population", 0)),
                v.get("status", ""),
            ]
            data.append(row)

        table = Table(
            data,
            colWidths=[
                0.4 * inch,
                1.2 * inch,
                0.8 * inch,
                0.8 * inch,
                0.8 * inch,
                0.6 * inch,
                0.6 * inch,
            ],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 30))

        footer = Paragraph(
            f"页脚 - 帮扶管理信息系统 - {datetime.now().year}",
            self.styles["Footer"],
        )
        elements.append(footer)

        doc.build(elements)
        return buffer.getvalue()

    def generate_projects_report(self, projects: List[Dict]) -> bytes:
        """生成项目报表PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        elements = []

        title = Paragraph("项目列表报表", self.styles["ReportTitle"])
        elements.append(title)

        subtitle = Paragraph(
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>" f"项目总数：{len(projects)}",
            self.styles["Normal_CN"],
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 20))

        headers = ["ID", "名称", "类型", "状态", "预算(万元)", "进度", "开始日期"]
        data = [[h for h in headers]]

        for p in projects:
            row = [
                str(p.get("id", "")),
                p.get("name", "")[:15] + ("..." if len(p.get("name", "")) > 15 else ""),
                p.get("type", "") or "-",
                p.get("status", ""),
                str(p.get("budget", 0) or 0),
                f"{p.get('progress', 0)}%",
                str(p.get("start_date", "") or "-")[:10],
            ]
            data.append(row)

        table = Table(
            data,
            colWidths=[
                0.4 * inch,
                1.8 * inch,
                0.8 * inch,
                0.6 * inch,
                0.8 * inch,
                0.5 * inch,
                0.8 * inch,
            ],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 30))

        footer = Paragraph(
            f"页脚 - 帮扶管理信息系统 - {datetime.now().year}",
            self.styles["Footer"],
        )
        elements.append(footer)

        doc.build(elements)
        return buffer.getvalue()

    def generate_funds_report(self, funds: List[Dict]) -> bytes:
        """生成经费报表PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        elements = []

        title = Paragraph("经费列表报表", self.styles["ReportTitle"])
        elements.append(title)

        total_amount = sum(f.get("amount", 0) for f in funds)
        subtitle = Paragraph(
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"经费总数：{len(funds)} | 总金额：{total_amount:.2f}元",
            self.styles["Normal_CN"],
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 20))

        headers = ["ID", "名称", "类型", "金额(元)", "来源", "状态", "申请人"]
        data = [[h for h in headers]]

        for f in funds:
            row = [
                str(f.get("id", "")),
                f.get("name", "")[:12] + ("..." if len(f.get("name", "")) > 12 else ""),
                f.get("type", "") or "-",
                f"{f.get('amount', 0):.2f}",
                f.get("source", "") or "-",
                f.get("status", ""),
                f.get("applicant", "") or "-",
            ]
            data.append(row)

        table = Table(
            data,
            colWidths=[
                0.4 * inch,
                1.5 * inch,
                0.6 * inch,
                0.8 * inch,
                0.8 * inch,
                0.6 * inch,
                0.6 * inch,
            ],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 30))

        footer = Paragraph(
            f"页脚 - 帮扶管理信息系统 - {datetime.now().year}",
            self.styles["Footer"],
        )
        elements.append(footer)

        doc.build(elements)
        return buffer.getvalue()

    def generate_comprehensive_report(self, summary: Dict[str, Any], sections: List[Dict[str, List[Dict]]]) -> bytes:
        """生成综合报表PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        elements = []

        title = Paragraph("综合统计报表", self.styles["ReportTitle"])
        elements.append(title)

        elements.append(Spacer(1, 10))

        elements.append(Paragraph("统计摘要", self.styles["SectionTitle"]))
        summary_data = [[k, str(v)] for k, v in summary.items()]
        summary_table = Table(summary_data, colWidths=[2 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(summary_table)

        for section in sections:
            elements.append(PageBreak())
            elements.append(Paragraph(section["title"], self.styles["SectionTitle"]))

            if "data" in section and section["data"]:
                headers = section.get("headers", [])
                data = [headers] if headers else []

                for item in section["data"][:50]:
                    row = [str(item.get(h, "")) for h in headers] if headers else list(item.values())
                    data.append(row)

                col_widths = section.get("col_widths", [1 * inch] * len(headers) if headers else [1 * inch])
                table = Table(data, colWidths=col_widths)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 9),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
                            ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ]
                    )
                )
                elements.append(table)

        elements.append(Spacer(1, 30))

        footer = Paragraph(
            f"页脚 - 帮扶管理信息系统 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles["Footer"],
        )
        elements.append(footer)

        doc.build(elements)
        return buffer.getvalue()


pdf_service = PDFReportService()


class PDFService:
    """向后兼容包装器 - 代理到 PDFReportService"""

    def __init__(self, db: Session = None):
        self.db = db
        self._service = pdf_service

    def generate_report(self, *args, **kwargs):
        return self._service.generate_executive_report(*args, **kwargs)

    @staticmethod
    def create(db: Session = None) -> "PDFService":
        return PDFService(db)
