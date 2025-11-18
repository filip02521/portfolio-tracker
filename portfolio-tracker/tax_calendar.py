"""
Tax Calendar System for Portfolio Tracker
"""
import json
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import calendar

class TaxCalendar:
    """System kalendarza podatkowego"""
    
    def __init__(self, calendar_file='tax_calendar.json'):
        self.calendar_file = calendar_file
        self.tax_dates = self.load_tax_dates()
    
    def load_tax_dates(self):
        """Load tax calendar dates"""
        if os.path.exists(self.calendar_file):
            try:
                with open(self.calendar_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default tax dates for Poland
        current_year = datetime.now().year
        default_dates = {
            str(current_year): {
                'tax_return_deadline': f"{current_year}-04-30",
                'tax_payment_deadline': f"{current_year}-05-31",
                'quarterly_payments': [
                    f"{current_year}-03-31",
                    f"{current_year}-05-31", 
                    f"{current_year}-08-31",
                    f"{current_year}-11-30"
                ],
                'important_dates': [
                    {
                        'date': f"{current_year}-01-31",
                        'description': 'Termin składania PIT-11 za poprzedni rok',
                        'type': 'deadline'
                    },
                    {
                        'date': f"{current_year}-02-15",
                        'description': 'Termin składania PIT-8AR za poprzedni rok',
                        'type': 'deadline'
                    },
                    {
                        'date': f"{current_year}-04-30",
                        'description': 'Termin składania zeznania podatkowego PIT-37',
                        'type': 'deadline'
                    },
                    {
                        'date': f"{current_year}-05-31",
                        'description': 'Termin zapłaty podatku dochodowego',
                        'type': 'payment'
                    },
                    {
                        'date': f"{current_year}-06-30",
                        'description': 'Termin składania PIT-11 za pierwszy kwartał',
                        'type': 'deadline'
                    },
                    {
                        'date': f"{current_year}-09-30",
                        'description': 'Termin składania PIT-11 za drugi kwartał',
                        'type': 'deadline'
                    },
                    {
                        'date': f"{current_year}-12-31",
                        'description': 'Termin składania PIT-11 za trzeci kwartał',
                        'type': 'deadline'
                    }
                ]
            }
        }
        
        self.save_tax_dates(default_dates)
        return default_dates
    
    def save_tax_dates(self, dates=None):
        """Save tax dates to file"""
        if dates is None:
            dates = self.tax_dates
        
        with open(self.calendar_file, 'w') as f:
            json.dump(dates, f, indent=2)
    
    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming tax deadlines"""
        upcoming = []
        today = datetime.now().date()
        cutoff_date = today + timedelta(days=days_ahead)
        
        current_year = str(datetime.now().year)
        year_dates = self.tax_dates.get(current_year, {})
        
        # Check important dates
        for date_info in year_dates.get('important_dates', []):
            deadline_date = datetime.strptime(date_info['date'], '%Y-%m-%d').date()
            
            if today <= deadline_date <= cutoff_date:
                days_until = (deadline_date - today).days
                
                upcoming.append({
                    'date': date_info['date'],
                    'description': date_info['description'],
                    'type': date_info['type'],
                    'days_until': days_until,
                    'is_overdue': False
                })
        
        # Check quarterly payments
        for quarter_date in year_dates.get('quarterly_payments', []):
            quarter_dt = datetime.strptime(quarter_date, '%Y-%m-%d').date()
            
            if today <= quarter_dt <= cutoff_date:
                days_until = (quarter_dt - today).days
                
                upcoming.append({
                    'date': quarter_date,
                    'description': f"Płatność kwartalna - {quarter_dt.strftime('%B %Y')}",
                    'type': 'payment',
                    'days_until': days_until,
                    'is_overdue': False
                })
        
        # Sort by date
        upcoming.sort(key=lambda x: x['date'])
        
        return upcoming
    
    def get_overdue_deadlines(self) -> List[Dict]:
        """Get overdue tax deadlines"""
        overdue = []
        today = datetime.now().date()
        
        current_year = str(datetime.now().year)
        year_dates = self.tax_dates.get(current_year, {})
        
        # Check important dates
        for date_info in year_dates.get('important_dates', []):
            deadline_date = datetime.strptime(date_info['date'], '%Y-%m-%d').date()
            
            if deadline_date < today:
                days_overdue = (today - deadline_date).days
                
                overdue.append({
                    'date': date_info['date'],
                    'description': date_info['description'],
                    'type': date_info['type'],
                    'days_overdue': days_overdue,
                    'is_overdue': True
                })
        
        # Check quarterly payments
        for quarter_date in year_dates.get('quarterly_payments', []):
            quarter_dt = datetime.strptime(quarter_date, '%Y-%m-%d').date()
            
            if quarter_dt < today:
                days_overdue = (today - quarter_dt).days
                
                overdue.append({
                    'date': quarter_date,
                    'description': f"Płatność kwartalna - {quarter_dt.strftime('%B %Y')}",
                    'type': 'payment',
                    'days_overdue': days_overdue,
                    'is_overdue': True
                })
        
        # Sort by days overdue (most overdue first)
        overdue.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        return overdue
    
    def get_tax_checklist(self) -> List[Dict]:
        """Get tax preparation checklist"""
        checklist = [
            {
                'task': 'Zebranie wszystkich dokumentów transakcyjnych',
                'description': 'Pobranie historii transakcji z wszystkich giełd',
                'completed': False,
                'priority': 'high'
            },
            {
                'task': 'Kalkulacja zrealizowanego PNL (FIFO)',
                'description': 'Obliczenie zysków/strat zgodnie z metodą FIFO',
                'completed': False,
                'priority': 'high'
            },
            {
                'task': 'Przeliczenie wartości na PLN',
                'description': 'Konwersja wszystkich transakcji na złotówki',
                'completed': False,
                'priority': 'high'
            },
            {
                'task': 'Sprawdzenie progów podatkowych',
                'description': 'Weryfikacja czy przekroczono próg 19% podatku',
                'completed': False,
                'priority': 'medium'
            },
            {
                'task': 'Przygotowanie dokumentacji',
                'description': 'Wydrukowanie raportów PDF do załączenia',
                'completed': False,
                'priority': 'medium'
            },
            {
                'task': 'Wypełnienie zeznania PIT-37',
                'description': 'Przeniesienie danych do formularza podatkowego',
                'completed': False,
                'priority': 'high'
            },
            {
                'task': 'Sprawdzenie poprawności danych',
                'description': 'Weryfikacja wszystkich obliczeń przed wysłaniem',
                'completed': False,
                'priority': 'high'
            },
            {
                'task': 'Wysłanie zeznania',
                'description': 'Elektroniczne lub papierowe złożenie zeznania',
                'completed': False,
                'priority': 'high'
            }
        ]
        
        return checklist
    
    def calculate_tax_estimate(self, realized_pnl: float) -> Dict:
        """Calculate estimated tax amount"""
        if realized_pnl <= 0:
            return {
                'taxable_amount': 0,
                'tax_rate': 0,
                'estimated_tax': 0,
                'message': 'Brak podatku - strata z inwestycji'
            }
        
        # Polish tax rates for capital gains
        if realized_pnl <= 10000:  # First threshold
            tax_rate = 0.19
            taxable_amount = realized_pnl
        else:
            tax_rate = 0.19
            taxable_amount = realized_pnl
        
        estimated_tax = taxable_amount * tax_rate
        
        return {
            'taxable_amount': taxable_amount,
            'tax_rate': tax_rate,
            'estimated_tax': estimated_tax,
            'message': f'Podatek do zapłacenia: {estimated_tax:,.2f} PLN'
        }
    
    def get_tax_tips(self) -> List[str]:
        """Get tax preparation tips"""
        tips = [
            "📋 Zachowaj wszystkie dokumenty transakcyjne przez 5 lat",
            "💰 Pamiętaj o metodzie FIFO przy kalkulacji PNL",
            "📊 Używaj kursów NBP z dnia transakcji",
            "⏰ Nie przegap terminu składania zeznania (30 kwietnia)",
            "💳 Przygotuj środki na zapłatę podatku (31 maja)",
            "🔍 Sprawdź czy nie przekroczyłeś progów podatkowych",
            "📄 Wydrukuj raporty PDF jako dokumentację",
            "✅ Weryfikuj wszystkie obliczenia przed wysłaniem",
            "💻 Rozważ elektroniczne składanie zeznania",
            "📞 W razie wątpliwości skonsultuj się z doradcą podatkowym"
        ]
        
        return tips
    
    def add_custom_deadline(self, date_str: str, description: str, deadline_type: str = 'deadline'):
        """Add custom deadline to calendar"""
        current_year = str(datetime.now().year)
        
        if current_year not in self.tax_dates:
            self.tax_dates[current_year] = {'important_dates': []}
        
        if 'important_dates' not in self.tax_dates[current_year]:
            self.tax_dates[current_year]['important_dates'] = []
        
        new_deadline = {
            'date': date_str,
            'description': description,
            'type': deadline_type
        }
        
        self.tax_dates[current_year]['important_dates'].append(new_deadline)
        self.save_tax_dates()
        
        print(f"✅ Dodano termin: {description} ({date_str})")

# Example usage
if __name__ == "__main__":
    # Test tax calendar
    tax_calendar = TaxCalendar()
    
    # Get upcoming deadlines
    upcoming = tax_calendar.get_upcoming_deadlines(60)
    print("Nadchodzące terminy:")
    for deadline in upcoming:
        print(f"• {deadline['description']} - {deadline['days_until']} dni")
    
    # Get overdue deadlines
    overdue = tax_calendar.get_overdue_deadlines()
    print(f"\nPrzeterminowane ({len(overdue)}):")
    for deadline in overdue:
        print(f"• {deadline['description']} - {deadline['days_overdue']} dni temu")
    
    # Get checklist
    checklist = tax_calendar.get_tax_checklist()
    print(f"\nChecklist podatkowy ({len(checklist)} zadań):")
    for i, task in enumerate(checklist, 1):
        print(f"{i}. {task['task']}")
    
    # Calculate tax estimate
    tax_estimate = tax_calendar.calculate_tax_estimate(5000)
    print(f"\nSzacunek podatku:")
    print(f"• Podstawa: {tax_estimate['taxable_amount']:,.2f} PLN")
    print(f"• Stawka: {tax_estimate['tax_rate']*100:.0f}%")
    print(f"• Podatek: {tax_estimate['estimated_tax']:,.2f} PLN")
    
    # Get tips
    tips = tax_calendar.get_tax_tips()
    print(f"\nWskazówki podatkowe:")
    for tip in tips[:5]:  # Show first 5 tips
        print(f"• {tip}")


