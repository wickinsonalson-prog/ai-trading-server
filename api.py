"""
AI Trading Signal Analyzer Server - FREE VERSION
Uses Hugging Face (100% Free) instead of paid APIs
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# Configuration - Hugging Face is FREE!
HF_API_TOKEN = os.environ.get('HF_API_TOKEN', 'your-token-here')
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

# Store recent analyses
recent_analyses = []

def analyze_with_free_ai(signal_data):
    """
    Use FREE Hugging Face AI to analyze the trading signal
    Model: Mistral-7B (Free, no credit card needed)
    """
    try:
        # Create comprehensive prompt for AI analysis
        prompt = f"""<s>[INST] You are an expert technical analyst. Analyze this trading signal and provide a confidence score.

Signal Data:
- Symbol: {signal_data.get('symbol')}
- Price: ${signal_data.get('price')}
- Signal Type: {signal_data.get('signal_type')}
- Base Confidence: {signal_data.get('confidence')}%

Technical Indicators:
- RSI: {signal_data.get('rsi')} (Overbought >70, Oversold <30)
- ADX: {signal_data.get('adx')} (Trend strength, >25 is strong)
- Volume Ratio: {signal_data.get('volume_ratio')}x (>1.5 is high)
- ATR%: {signal_data.get('atr_percent')}%
- VWAP Position: {signal_data.get('vwap_position')}

Waddah Attar: Bullish={signal_data.get('waddah_bullish')}, Bearish={signal_data.get('waddah_bearish')}, Explosive={signal_data.get('waddah_explosive')}
Squeeze: Status={signal_data.get('squeeze_status')}, Momentum={signal_data.get('squeeze_momentum')}
Supertrend: {signal_data.get('supertrend')}, MFI: {signal_data.get('mfi')}, Fisher: {signal_data.get('fisher')}
Market: EMA={signal_data.get('ema_alignment')}, HTF={signal_data.get('htf_trend')}, Pattern={signal_data.get('pattern')}

Provide analysis in this EXACT format:
CONFIDENCE: [number 0-100]
RECOMMENDATION: [BUY/SELL/WAIT]
RISK: [LOW/MEDIUM/HIGH]
STRENGTHS: [list 2-3 key strengths]
CONCERNS: [list 1-2 concerns]
REASON: [1-2 sentence explanation] [/INST]"""

        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.3,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        # Call Hugging Face API
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
            
            # Parse AI response
            confidence = 70  # Default
            recommendation = "WAIT"
            risk_level = "MEDIUM"
            strengths = []
            concerns = []
            reasoning = "Analysis complete"
            
            # Extract values from response
            lines = ai_text.split('\n')
            for line in lines:
                line = line.strip()
                if 'CONFIDENCE:' in line.upper():
                    try:
                        confidence = int(''.join(filter(str.isdigit, line)))
                    except:
                        pass
                elif 'RECOMMENDATION:' in line.upper():
                    if 'BUY' in line.upper():
                        recommendation = 'BUY'
                    elif 'SELL' in line.upper():
                        recommendation = 'SELL'
                    else:
                        recommendation = 'WAIT'
                elif 'RISK:' in line.upper():
                    if 'LOW' in line.upper():
                        risk_level = 'LOW'
                    elif 'HIGH' in line.upper():
                        risk_level = 'HIGH'
                    else:
                        risk_level = 'MEDIUM'
                elif 'STRENGTHS:' in line.upper():
                    strengths_text = line.split(':', 1)[1] if ':' in line else ''
                    strengths = [s.strip() for s in strengths_text.split(',') if s.strip()]
                elif 'CONCERNS:' in line.upper():
                    concerns_text = line.split(':', 1)[1] if ':' in line else ''
                    concerns = [c.strip() for c in concerns_text.split(',') if c.strip()]
                elif 'REASON:' in line.upper():
                    reasoning = line.split(':', 1)[1].strip() if ':' in line else line
            
            # If parsing failed, use basic heuristics
            if not strengths:
                strengths = ["Strong momentum" if signal_data.get('adx', 0) > 25 else "Moderate setup"]
            if not concerns:
                concerns = ["Monitor risk levels"]
            if len(reasoning) < 10:
                reasoning = f"Signal shows {recommendation.lower()} potential with {confidence}% confidence"
            
            return {
                "success": True,
                "ai_confidence": min(max(confidence, 0), 100),
                "recommendation": recommendation,
                "risk_level": risk_level,
                "key_strengths": strengths[:3],
                "concerns": concerns[:2],
                "reasoning": reasoning,
                "timestamp": datetime.utcnow().isoformat(),
                "model": "Mistral-7B-Free"
            }
        
        elif response.status_code == 503:
            # Model is loading, use fallback logic
            return use_fallback_analysis(signal_data)
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return use_fallback_analysis(signal_data)
            
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return use_fallback_analysis(signal_data)

def use_fallback_analysis(signal_data):
    """
    Fallback logic-based analysis when AI is unavailable
    """
    confidence = signal_data.get('confidence', 70)
    signal_type = signal_data.get('signal_type', 'BUY')
    rsi = signal_data.get('rsi', 50)
    adx = signal_data.get('adx', 20)
    volume_ratio = signal_data.get('volume_ratio', 1.0)
    
    # Calculate adjusted confidence
    if adx > 25:
        confidence += 5
    if volume_ratio > 1.5:
        confidence += 5
    if signal_type == 'BUY' and rsi < 30:
        confidence += 10
    elif signal_type == 'SELL' and rsi > 70:
        confidence += 10
    
    confidence = min(confidence, 100)
    
    # Determine risk level
    if confidence > 80 and adx > 30:
        risk_level = "LOW"
    elif confidence < 65 or adx < 20:
        risk_level = "HIGH"
    else:
        risk_level = "MEDIUM"
    
    # Determine recommendation
    if confidence >= 75:
        recommendation = signal_type
    else:
        recommendation = "WAIT"
    
    strengths = []
    if adx > 25:
        strengths.append("Strong trend")
    if volume_ratio > 1.5:
        strengths.append("High volume confirmation")
    if (signal_type == 'BUY' and rsi < 50) or (signal_type == 'SELL' and rsi > 50):
        strengths.append("Good momentum")
    
    concerns = []
    if adx < 20:
        concerns.append("Weak trend strength")
    if volume_ratio < 1.2:
        concerns.append("Low volume")
    
    return {
        "success": True,
        "ai_confidence": confidence,
        "recommendation": recommendation,
        "risk_level": risk_level,
        "key_strengths": strengths if strengths else ["Setup detected"],
        "concerns": concerns if concerns else ["Monitor market conditions"],
        "reasoning": f"Logic-based analysis: {recommendation} signal with {confidence}% confidence",
        "timestamp": datetime.utcnow().isoformat(),
        "model": "Fallback-Logic"
    }

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "service": "AI Trading Signal Analyzer (FREE)",
        "version": "2.0-Free",
        "ai_model": "Hugging Face Mistral-7B (Free)",
        "endpoints": {
            "/analyze": "POST - Analyze trading signal",
            "/history": "GET - View recent analyses",
            "/health": "GET - Service health check",
            "/test": "POST - Test with sample data"
        }
    })

@app.route('/health')
def health():
    """Health check for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_provider": "Hugging Face (FREE)"
    })

@app.route('/analyze', methods=['POST'])
def analyze_signal():
    """
    Main endpoint to receive and analyze trading signals
    Receives JSON webhook from TradingView
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data received"
            }), 400
        
        print(f"📊 Received signal: {data.get('symbol')} - {data.get('signal_type')}")
        
        # Analyze with FREE AI
        ai_result = analyze_with_free_ai(data)
        
        # Combine original signal with AI analysis
        result = {
            "original_signal": {
                "symbol": data.get('symbol'),
                "price": data.get('price'),
                "signal_type": data.get('signal_type'),
                "base_confidence": data.get('confidence')
            },
            "ai_analysis": ai_result,
            "final_decision": {
                "should_trade": ai_result.get('ai_confidence', 0) >= 70 and 
                               ai_result.get('recommendation') in ['BUY', 'SELL'],
                "combined_confidence": (data.get('confidence', 0) + ai_result.get('ai_confidence', 0)) / 2,
                "recommendation": ai_result.get('recommendation'),
                "risk_level": ai_result.get('risk_level')
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in recent analyses (keep last 100)
        recent_analyses.append(result)
        if len(recent_analyses) > 100:
            recent_analyses.pop(0)
        
        print(f"✅ Analysis complete: {ai_result.get('recommendation')} - {ai_result.get('ai_confidence')}%")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error processing signal: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get recent signal analyses"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        "total": len(recent_analyses),
        "analyses": recent_analyses[-limit:]
    })

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint with sample data"""
    sample_data = {
        "symbol": "BTCUSD",
        "price": 45000,
        "signal_type": "BUY",
        "confidence": 75,
        "rsi": 45,
        "adx": 28,
        "volume_ratio": 1.8,
        "atr_percent": 2.5,
        "vwap_position": "above",
        "waddah_bullish": 80,
        "waddah_bearish": 20,
        "waddah_explosive": True,
        "squeeze_status": "firing",
        "squeeze_momentum": "bullish",
        "supertrend": "bullish",
        "mfi": 55,
        "fisher": "rising",
        "ema_alignment": "bullish",
        "htf_trend": "up",
        "pattern": "higher_highs"
    }
    
    ai_result = analyze_with_free_ai(sample_data)
    
    return jsonify({
        "test": "successful",
        "sample_data": sample_data,
        "ai_analysis": ai_result,
        "note": "Using FREE Hugging Face AI - No costs!"
    })

if __name__ == '__main__':
    print("🚀 AI Trading Signal Analyzer Starting (FREE VERSION)...")
    print("🤖 Using Hugging Face Mistral-7B (100% FREE)")
    print("📡 Endpoints:")
    print("   POST /analyze - Analyze trading signals")
    print("   GET  /history - View recent analyses")
    print("   POST /test    - Test with sample data")
    print("   GET  /health  - Health check")
    print("\n💡 Get FREE Hugging Face token at: https://huggingface.co/settings/tokens")
    print("   Or leave empty to use fallback logic-based analysis\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)