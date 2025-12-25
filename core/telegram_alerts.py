"""
Telegram Alert System
Sends trading signals and notifications via Telegram bot
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
import json


class TelegramAlert:
    """
    Professional Telegram notification system for trading alerts.
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram Alert System.
        
        Args:
            bot_token: Telegram bot token (from BotFather)
            chat_id: Your Telegram chat ID
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def _send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Send a message via Telegram bot.
        
        Args:
            text: Message text
            parse_mode: 'HTML' or 'Markdown'
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            return False
            
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    def send_opportunity_alert(self, 
                              symbol: str,
                              score: float,
                              direction: str,
                              entry_zone: Dict,
                              confluence: Dict,
                              checklist: Dict) -> bool:
        """
        Send a formatted trading opportunity alert.
        
        Args:
            symbol: Trading pair
            score: Opportunity score (0-100)
            direction: 'LONG' or 'SHORT'
            entry_zone: Entry zone details
            confluence: Confluence score details
            checklist: Confirmation checklist
            
        Returns:
            True if sent successfully
        """
        # Emoji based on score
        if score >= 75:
            emoji = "🔥"
            strength = "STRONG"
        elif score >= 60:
            emoji = "✅"
            strength = "GOOD"
        else:
            emoji = "⚡"
            strength = "MODERATE"
        
        # Direction emoji
        dir_emoji = "🚀" if direction == "LONG" else "🔻"
        
        message = f"""
{emoji} <b>TRADING OPPORTUNITY</b> {emoji}

{dir_emoji} <b>{symbol}</b> - {direction} {strength}
━━━━━━━━━━━━━━━━━━━━

<b>📊 SCORE: {score}/100</b>

<b>💰 ENTRY ZONE:</b>
├ Aggressive: ${entry_zone.get('aggressive_entry', 0):.6f}
├ Optimal: ${entry_zone.get('optimal_entry', 0):.6f}
└ Conservative: ${entry_zone.get('conservative_entry', 0):.6f}

<b>🛡 RISK MANAGEMENT:</b>
├ ATR Stop: ${entry_zone.get('atr_stop_loss', 0):.6f}
└ Invalidation: ${entry_zone.get('invalidation_level', 0):.6f}

<b>📈 TIMEFRAME CONFLUENCE:</b>
"""
        
        # Add timeframe details
        for tf_detail in confluence.get('timeframe_details', []):
            tf_name = tf_detail['timeframe']
            tf_score = tf_detail['weighted_score']
            trend = tf_detail['trend']
            structure = tf_detail['market_structure']
            
            trend_emoji = "🟢" if trend == "BULLISH" else "🔴" if trend == "BEARISH" else "🟡"
            message += f"├ {tf_name.upper()}: {trend_emoji} {trend} | {structure} ({tf_score:.1f}pts)\n"
        
        message += "\n<b>✓ CONFIRMATIONS:</b>\n"
        
        # Add checklist (only show passed items to keep message short)
        passed_items = [item for item in checklist.get('checklist', []) if item['passed']]
        for item in passed_items[:8]:  # Show top 8 confirmations
            message += f"├ ✓ {item['item']}\n"
        
        pass_rate = checklist.get('pass_rate', 0)
        message += f"\n<b>Pass Rate: {pass_rate:.0f}%</b> ({checklist.get('passed')}/{checklist.get('total')})\n"
        
        message += f"\n⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        return self._send_message(message)
    
    def send_position_alert(self,
                           action: str,
                           symbol: str,
                           side: str,
                           contracts: int,
                           entry_price: float,
                           stop_loss: float,
                           take_profits: List[Dict],
                           leverage: int,
                           risk_pct: float) -> bool:
        """
        Send position opened/closed alert.
        
        Args:
            action: 'OPENED' or 'CLOSED'
            symbol: Trading pair
            side: 'LONG' or 'SHORT'
            contracts: Number of contracts
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profits: List of TP targets
            leverage: Leverage used
            risk_pct: Risk percentage
            
        Returns:
            True if sent successfully
        """
        if action == 'OPENED':
            emoji = "🎯"
            color = "GREEN" if side == "LONG" else "RED"
        else:
            emoji = "🏁"
            color = "BLUE"
        
        side_emoji = "🚀" if side == "LONG" else "🔻"
        
        message = f"""
{emoji} <b>POSITION {action}</b> {emoji}

{side_emoji} <b>{symbol}</b> - {side}
━━━━━━━━━━━━━━━━━━━━

<b>📋 DETAILS:</b>
├ Contracts: {contracts}
├ Entry: ${entry_price:.6f}
├ Leverage: {leverage}x
└ Risk: {risk_pct:.2f}%

<b>🛡 STOP LOSS:</b>
└ ${stop_loss:.6f} ({abs((stop_loss-entry_price)/entry_price*100):.2f}%)

<b>🎯 TAKE PROFITS:</b>
"""
        
        for tp in take_profits:
            tp_pct = tp.get('profit_pct', 0)
            tp_price = tp.get('price', 0)
            tp_level = tp.get('level', 0)
            message += f"├ TP{tp_level}: ${tp_price:.6f} (+{tp_pct:.2f}%)\n"
        
        message += f"\n⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        return self._send_message(message)
    
    def send_risk_alert(self,
                       alert_type: str,
                       details: str) -> bool:
        """
        Send risk management alerts.
        
        Args:
            alert_type: Type of risk alert
            details: Alert details
            
        Returns:
            True if sent successfully
        """
        message = f"""
⚠️ <b>RISK ALERT</b> ⚠️

<b>Type:</b> {alert_type}

{details}

⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        
        return self._send_message(message)
    
    def send_position_update(self,
                            symbol: str,
                            side: str,
                            entry_price: float,
                            current_price: float,
                            pnl_pct: float,
                            pnl_usd: float,
                            suggestion: str) -> bool:
        """
        Send position update with P&L.
        
        Args:
            symbol: Trading pair
            side: 'LONG' or 'SHORT'
            entry_price: Entry price
            current_price: Current price
            pnl_pct: P&L percentage
            pnl_usd: P&L in USD
            suggestion: Management suggestion
            
        Returns:
            True if sent successfully
        """
        pnl_emoji = "💰" if pnl_pct > 0 else "📉"
        side_emoji = "🚀" if side == "LONG" else "🔻"
        
        message = f"""
{pnl_emoji} <b>POSITION UPDATE</b>

{side_emoji} <b>{symbol}</b> - {side}
━━━━━━━━━━━━━━━━━━━━

<b>📊 PERFORMANCE:</b>
├ Entry: ${entry_price:.6f}
├ Current: ${current_price:.6f}
├ P&L: {pnl_pct:+.2f}%
└ P&L USD: ${pnl_usd:+.2f}

<b>💡 SUGGESTION:</b>
{suggestion}

⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
        
        return self._send_message(message)
    
    def send_daily_summary(self,
                          trades_today: int,
                          wins: int,
                          losses: int,
                          pnl_today: float,
                          total_pnl: float,
                          win_rate: float) -> bool:
        """
        Send daily trading summary.
        
        Args:
            trades_today: Number of trades today
            wins: Winning trades
            losses: Losing trades
            pnl_today: Today's P&L
            total_pnl: Total P&L
            win_rate: Win rate percentage
            
        Returns:
            True if sent successfully
        """
        emoji = "🎉" if pnl_today > 0 else "📊"
        
        message = f"""
{emoji} <b>DAILY SUMMARY</b> {emoji}

📅 <b>{datetime.now().strftime('%Y-%m-%d')}</b>
━━━━━━━━━━━━━━━━━━━━

<b>📊 STATISTICS:</b>
├ Trades: {trades_today}
├ Wins: {wins} ✅
├ Losses: {losses} ❌
└ Win Rate: {win_rate:.1f}%

<b>💰 P&L:</b>
├ Today: ${pnl_today:+.2f}
└ Total: ${total_pnl:+.2f}

⏰ <i>{datetime.now().strftime('%H:%M:%S')}</i>
"""
        
        return self._send_message(message)
    
    def send_test_message(self) -> bool:
        """
        Send a test message to verify configuration.
        
        Returns:
            True if sent successfully
        """
        message = """
🤖 <b>HekstTradeHub Alert System</b>

✅ Telegram alerts configured successfully!

You will receive notifications for:
├ Trading opportunities
├ Position management
├ Risk alerts
└ Daily summaries

⏰ <i>Ready to trade!</i>
"""
        
        return self._send_message(message)


def setup_telegram_instructions():
    """
    Print instructions for setting up Telegram bot.
    """
    print("""
╔════════════════════════════════════════════════════════════════╗
║           TELEGRAM ALERT SETUP INSTRUCTIONS                    ║
╚════════════════════════════════════════════════════════════════╝

1️⃣  CREATE BOT:
   └ Open Telegram and search for @BotFather
   └ Send: /newbot
   └ Follow instructions to create your bot
   └ Save the BOT TOKEN

2️⃣  GET YOUR CHAT ID:
   └ Search for @userinfobot in Telegram
   └ Start the bot
   └ It will send you your CHAT ID

3️⃣  ADD TO .ENV FILE:
   └ Add these lines to /home/hektic/hekstradehub/.env:
   
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here

4️⃣  TEST:
   └ Run: python -c "from core.telegram_alerts import TelegramAlert; TelegramAlert().send_test_message()"

╚════════════════════════════════════════════════════════════════╝
    """)


if __name__ == '__main__':
    # Show setup instructions if running directly
    setup_telegram_instructions()
    
    # Try to send test message if configured
    alert = TelegramAlert()
    if alert.bot_token and alert.chat_id:
        print("\nSending test message...")
        if alert.send_test_message():
            print("✅ Test message sent successfully!")
        else:
            print("❌ Failed to send test message")
    else:
        print("\n⚠️  Telegram not configured yet. Follow instructions above.")
