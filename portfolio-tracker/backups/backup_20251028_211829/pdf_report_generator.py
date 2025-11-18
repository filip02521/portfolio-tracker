"""
PDF Report Generator for Tax Reports
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

class PDFReportGenerator:
    """Generate PDF reports for tax purposes"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_tax_report_pdf(self, year: int, transactions_data: list, filename: str = None):
        """Generate comprehensive tax report PDF"""
        
        if filename is None:
            filename = f"tax_report_{year}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph(f"Raport Podatkowy {year}", self.styles['CustomTitle'])
        story.append(title)
        
        # Report info
        report_date = datetime.now().strftime("%d.%m.%Y")
        info_text = f"Wygenerowano: {report_date}<br/>Rok podatkowy: {year}<br/>Metoda: FIFO (First In First Out)"
        info = Paragraph(info_text, self.styles['CustomBody'])
        story.append(info)
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Podsumowanie", self.styles['CustomHeading']))
        
        # Calculate summary data
        total_transactions = len(transactions_data)
        total_buys = len([t for t in transactions_data if t['type'] == 'buy'])
        total_sells = len([t for t in transactions_data if t['type'] == 'sell'])
        
        # Calculate realized PNL (simplified for PDF)
        realized_pnl = 0
        for tx in transactions_data:
            if tx['type'] == 'sell':
                # Simplified calculation for PDF display
                realized_pnl += tx.get('realized_pnl', 0)
        
        tax_due = realized_pnl * 0.19 if realized_pnl > 0 else 0
        
        # Summary table
        summary_data = [
            ['Metryka', 'Wartość'],
            ['Całkowite transakcje', str(total_transactions)],
            ['Zakupy', str(total_buys)],
            ['Sprzedaże', str(total_sells)],
            ['Zrealizowany PNL', f"${realized_pnl:,.2f}"],
            ['Podatek do zapłacenia (19%)', f"${tax_due:,.2f}" if tax_due > 0 else "Brak podatku"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Transactions section
        story.append(Paragraph("Szczegółowe Transakcje", self.styles['CustomHeading']))
        
        # Prepare transactions table
        tx_data = [['Data', 'Giełda', 'Aktywo', 'Typ', 'Ilość', 'Cena USD', 'Wartość USD', 'Kurs PLN', 'Wartość PLN']]
        
        for tx in transactions_data[:50]:  # Limit to first 50 transactions for PDF
            date_str = tx['date'][:10] if tx.get('date') else 'N/A'
            tx_type = 'Kupno' if tx['type'] == 'buy' else 'Sprzedaż'
            exchange_rate = f"{tx.get('exchange_rate_usd_pln', 0):.4f}" if tx.get('exchange_rate_usd_pln') else 'N/A'
            value_pln = f"{tx.get('value_pln', 0):,.2f}" if tx.get('value_pln') else 'N/A'
            
            tx_data.append([
                date_str,
                tx.get('exchange', 'N/A'),
                tx.get('asset', 'N/A'),
                tx_type,
                f"{tx.get('amount', 0):,.4f}",
                f"${tx.get('price_usd', 0):,.2f}",
                f"${tx.get('value_usd', 0):,.2f}",
                exchange_rate,
                f"{value_pln} PLN" if value_pln != 'N/A' else 'N/A'
            ])
        
        # Create transactions table
        tx_table = Table(tx_data, colWidths=[0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        story.append(tx_table)
        
        if len(transactions_data) > 50:
            story.append(Spacer(1, 10))
            note = Paragraph(f"<i>Uwaga: Pokazano pierwsze 50 transakcji z {len(transactions_data)} dostępnych.</i>", self.styles['CustomBody'])
            story.append(note)
        
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"Raport wygenerowany automatycznie przez Portfolio Tracker<br/>Data: {report_date}<br/>Metoda FIFO zgodna z polskim prawem podatkowym"
        footer = Paragraph(footer_text, self.styles['CustomBody'])
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF report generated: {filename}")
        return filename
    
    def generate_portfolio_summary_pdf(self, portfolio_data: dict, filename: str = None):
        """Generate portfolio summary PDF"""
        
        if filename is None:
            filename = f"portfolio_summary_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph("Podsumowanie Portfolio", self.styles['CustomTitle'])
        story.append(title)
        
        # Report info
        report_date = datetime.now().strftime("%d.%m.%Y")
        info_text = f"Wygenerowano: {report_date}<br/>Wartość portfolio: ${portfolio_data.get('total_value', 0):,.2f}"
        info = Paragraph(info_text, self.styles['CustomBody'])
        story.append(info)
        story.append(Spacer(1, 20))
        
        # Portfolio allocation
        story.append(Paragraph("Alokacja Portfolio", self.styles['CustomHeading']))
        
        # Create allocation table
        allocation_data = [['Giełda', 'Wartość USD', 'Procent']]
        
        for exchange, data in portfolio_data.get('exchanges', {}).items():
            allocation_data.append([
                exchange,
                f"${data.get('value', 0):,.2f}",
                f"{data.get('percentage', 0):.2f}%"
            ])
        
        allocation_table = Table(allocation_data, colWidths=[2*inch, 2*inch, 1*inch])
        allocation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(allocation_table)
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ Portfolio summary PDF generated: {filename}")
        return filename

# Example usage
if __name__ == "__main__":
    from transaction_history import TransactionHistory
    
    # Test PDF generation
    th = TransactionHistory()
    transactions = th.get_all_transactions()
    
    # Filter for 2024
    transactions_2024 = [t for t in transactions if t['date'][:4] == '2024']
    
    generator = PDFReportGenerator()
    generator.generate_tax_report_pdf(2024, transactions_2024)
