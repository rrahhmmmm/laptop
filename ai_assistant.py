"""
AI Assistant Module for Laptop Recommendation
Menggunakan ApiFreeLLM - Free LLM API tanpa API key
"""

import requests
import json
import re
from typing import Optional


# API Configuration
API_URL = "https://apifreellm.com/api/chat"
TIMEOUT = 60  # seconds

# System prompt untuk AI
SYSTEM_PROMPT = """Kamu adalah asisten AI untuk merekomendasikan laptop. Tugasmu adalah:
1. Memahami kebutuhan user dari chat mereka
2. Menentukan filter dan bobot prioritas untuk pencarian laptop

KRITERIA YANG TERSEDIA:
- price: Harga laptop (COST - semakin murah semakin baik)
- ram: Kapasitas RAM dalam GB (BENEFIT - semakin besar semakin baik)
- ssd: Kapasitas storage dalam GB (BENEFIT - semakin besar semakin baik)
- rating: Rating laptop 0-100 (BENEFIT - semakin tinggi semakin baik)
- display: Ukuran layar dalam inch (BENEFIT - semakin besar semakin baik)
- gpu: VRAM GPU dalam GB, 0 = integrated (BENEFIT - semakin besar semakin baik)

DATA YANG TERSEDIA:
{data_context}

MAPPING KEBUTUHAN:
- Gaming/Game: GPU tinggi (>=4GB), RAM tinggi (>=16GB), Display besar
- Editing Video/Render/3D: GPU sangat tinggi, RAM sangat tinggi (>=16GB), SSD besar
- Programming/Coding: RAM tinggi, SSD cepat, Display sedang-besar
- Office/Kerja Kantor: RAM sedang (8GB cukup), SSD sedang, Harga terjangkau
- Kuliah/Mahasiswa/Pelajar: Harga murah, RAM cukup, portabel (display kecil-sedang)
- Desain Grafis: GPU dedicated, RAM tinggi, Display bagus
- Browsing/Casual: Harga murah, spek standar

INSTRUKSI:
Analisis pesan user dan kembalikan response dalam format JSON VALID berikut:
{{
  "understood": true,
  "use_case": "deskripsi singkat kebutuhan",
  "response_message": "pesan balasan untuk user dalam Bahasa Indonesia yang ramah",
  "filters": {{
    "price_max": angka dalam rupiah atau null,
    "price_min": angka dalam rupiah atau null,
    "ram_min": angka GB atau null,
    "ram_max": angka GB atau null,
    "ssd_min": angka GB atau null,
    "gpu_min": angka GB atau null,
    "rating_min": angka 0-100 atau null,
    "display_min": angka inch atau null,
    "display_max": angka inch atau null
  }},
  "weights": {{
    "price": angka 1-5,
    "ram": angka 1-5,
    "ssd": angka 1-5,
    "rating": angka 1-5,
    "display": angka 1-5,
    "gpu": angka 1-5
  }}
}}

PENTING:
- Semua angka harga dalam RUPIAH (bukan juta, tulis lengkap misal 15000000)
- Bobot 1-5 dimana 5 = sangat penting, 1 = tidak penting
- Jika user tidak menyebut kriteria tertentu, gunakan nilai default atau null
- response_message harus ramah dan informatif
- SELALU kembalikan JSON yang valid
"""


def get_data_context(data_stats: dict) -> str:
    """Generate data context string for the prompt"""
    price_min_idr = int(data_stats['price']['min'] * 192)
    price_max_idr = int(data_stats['price']['max'] * 192)

    context = f"""
- Harga: Rp {price_min_idr:,} - Rp {price_max_idr:,}
- RAM: {', '.join([f'{x}GB' for x in data_stats['ram']['options']])}
- SSD: {', '.join([f'{x}GB' for x in data_stats['ssd']['options']])}
- Display: {data_stats['display']['min']:.1f}" - {data_stats['display']['max']:.1f}"
- GPU VRAM: {', '.join([f'{x}GB' if x > 0 else 'Integrated' for x in data_stats['gpu']['options']])}
- Rating: {data_stats['rating']['min']:.0f} - {data_stats['rating']['max']:.0f}
""".replace(",", ".")

    return context


def call_free_llm(message: str) -> dict:
    """
    Call ApiFreeLLM API

    Returns:
        dict with keys: success, response, error
    """
    try:
        response = requests.post(
            API_URL,
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        response.raise_for_status()

        # Try to parse JSON response
        try:
            data = response.json()
            # ApiFreeLLM might return response in different formats
            if isinstance(data, dict):
                # If it has a 'response' or 'message' key
                text = data.get('response') or data.get('message') or data.get('text') or str(data)
            else:
                text = str(data)
        except:
            text = response.text

        return {"success": True, "response": text}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout. Silakan coba lagi."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Tidak dapat terhubung ke server AI."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_user_message(message: str, data_stats: dict) -> dict:
    """
    Parse user message using ApiFreeLLM and return filters + weights

    Returns:
        dict with keys: success, response_message, filters, weights, error
    """
    result = {
        "success": False,
        "response_message": "",
        "filters": {},
        "weights": {},
        "error": None
    }

    # Build the full prompt
    data_context = get_data_context(data_stats)
    full_prompt = SYSTEM_PROMPT.format(data_context=data_context) + f"\n\nUser: {message}\n\nResponse (JSON only):"

    # Call the API
    api_result = call_free_llm(full_prompt)

    if not api_result["success"]:
        result["error"] = api_result["error"]
        result["response_message"] = f"Maaf, terjadi kesalahan: {api_result['error']}"
        return result

    response_text = api_result["response"]

    # Try to extract JSON from response
    try:
        # Find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            parsed = json.loads(json_str)

            if parsed.get("understood", True):
                result["success"] = True
                result["response_message"] = parsed.get("response_message", "Saya sudah menganalisis kebutuhan Anda.")
                result["filters"] = parsed.get("filters", {})
                result["weights"] = parsed.get("weights", {
                    "price": 3, "ram": 3, "ssd": 3,
                    "rating": 3, "display": 3, "gpu": 3
                })
                result["use_case"] = parsed.get("use_case", "")
            else:
                result["success"] = False
                result["response_message"] = parsed.get("response_message",
                    "Maaf, saya kurang memahami kebutuhan Anda. Bisa dijelaskan lebih detail?")
        else:
            # If no JSON found, use default response with simple parsing
            result = parse_simple_fallback(message, data_stats, response_text)

    except json.JSONDecodeError:
        # Fallback to simple parsing
        result = parse_simple_fallback(message, data_stats, response_text)
    except Exception as e:
        result["error"] = str(e)
        result["response_message"] = "Maaf, terjadi kesalahan dalam memproses permintaan."

    return result


def parse_simple_fallback(message: str, data_stats: dict, ai_response: str = "") -> dict:
    """
    Simple fallback parser when AI doesn't return proper JSON
    Uses keyword matching to determine filters and weights
    """
    message_lower = message.lower()

    # Default weights
    weights = {
        "price": 3, "ram": 3, "ssd": 3,
        "rating": 3, "display": 3, "gpu": 3
    }

    filters = {}

    # Parse budget
    budget_match = re.search(r'(\d+)\s*(juta|jt|million|m\b)', message_lower)
    if budget_match:
        budget = int(budget_match.group(1)) * 1000000
        filters["price_max"] = budget

    # Parse use case and set weights
    if any(word in message_lower for word in ['gaming', 'game', 'main game']):
        weights = {"price": 2, "ram": 4, "ssd": 3, "rating": 3, "display": 4, "gpu": 5}
        filters["gpu_min"] = 4
        filters["ram_min"] = 16

    elif any(word in message_lower for word in ['editing', 'edit', 'video', 'render', '3d', 'desain']):
        weights = {"price": 2, "ram": 5, "ssd": 4, "rating": 3, "display": 4, "gpu": 5}
        filters["gpu_min"] = 4
        filters["ram_min"] = 16
        filters["ssd_min"] = 512

    elif any(word in message_lower for word in ['programming', 'coding', 'developer', 'programmer', 'ngoding']):
        weights = {"price": 3, "ram": 5, "ssd": 4, "rating": 3, "display": 4, "gpu": 2}
        filters["ram_min"] = 16
        filters["ssd_min"] = 512

    elif any(word in message_lower for word in ['office', 'kantor', 'kerja', 'bisnis']):
        weights = {"price": 4, "ram": 3, "ssd": 3, "rating": 4, "display": 3, "gpu": 1}
        filters["ram_min"] = 8

    elif any(word in message_lower for word in ['kuliah', 'mahasiswa', 'pelajar', 'sekolah', 'student']):
        weights = {"price": 5, "ram": 3, "ssd": 3, "rating": 3, "display": 2, "gpu": 1}
        filters["ram_min"] = 8

    elif any(word in message_lower for word in ['murah', 'budget', 'hemat', 'terjangkau']):
        weights = {"price": 5, "ram": 3, "ssd": 2, "rating": 3, "display": 2, "gpu": 1}

    # Generate response message
    if ai_response and len(ai_response) > 20:
        response_message = ai_response[:500]  # Truncate if too long
    else:
        use_case = "kebutuhan Anda"
        if filters.get("price_max"):
            budget_str = f"Rp {filters['price_max']:,.0f}".replace(",", ".")
            response_message = f"Baik, saya akan carikan laptop untuk {use_case} dengan budget maksimal {budget_str}."
        else:
            response_message = f"Baik, saya akan carikan laptop yang cocok untuk {use_case}."

        if filters.get("ram_min"):
            response_message += f" RAM minimal {filters['ram_min']}GB."
        if filters.get("gpu_min"):
            response_message += f" GPU dedicated minimal {filters['gpu_min']}GB."

    return {
        "success": True,
        "response_message": response_message,
        "filters": filters,
        "weights": weights,
        "use_case": "parsed from keywords",
        "error": None
    }


def convert_ai_filters_to_app_filters(ai_filters: dict, data_stats: dict) -> dict:
    """
    Convert AI-generated filters to app filter format
    """
    # Get data ranges
    price_min_idr = int(data_stats['price']['min'] * 192)
    price_max_idr = int(data_stats['price']['max'] * 192)
    ram_options = data_stats['ram']['options']
    ssd_options = data_stats['ssd']['options']
    gpu_options = data_stats['gpu']['options']

    # Build app filters (converting IDR to INR for internal use)
    app_filters = {
        'price': (
            (ai_filters.get('price_min', price_min_idr) or price_min_idr) / 192,
            (ai_filters.get('price_max', price_max_idr) or price_max_idr) / 192
        ),
        'ram': (
            ai_filters.get('ram_min') or min(ram_options),
            ai_filters.get('ram_max') or max(ram_options)
        ),
        'ssd': (
            ai_filters.get('ssd_min') or min(ssd_options),
            max(ssd_options)
        ),
        'rating': (
            ai_filters.get('rating_min') or int(data_stats['rating']['min']),
            int(data_stats['rating']['max'])
        ),
        'display': (
            ai_filters.get('display_min') or float(data_stats['display']['min']),
            ai_filters.get('display_max') or float(data_stats['display']['max'])
        ),
        'gpu': (
            ai_filters.get('gpu_min') or min(gpu_options),
            max(gpu_options)
        )
    }

    return app_filters


def convert_ai_weights_to_app_weights(ai_weights: dict) -> dict:
    """
    Convert AI star ratings (1-5) to normalized weights for SAW
    """
    # Map star ratings to weight values
    star_to_weight = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20, 5: 0.25}

    raw_weights = {
        'price_numeric': star_to_weight.get(ai_weights.get('price', 3), 0.15),
        'ram_numeric': star_to_weight.get(ai_weights.get('ram', 3), 0.15),
        'ssd_numeric': star_to_weight.get(ai_weights.get('ssd', 3), 0.15),
        'rating_numeric': star_to_weight.get(ai_weights.get('rating', 3), 0.15),
        'display_numeric': star_to_weight.get(ai_weights.get('display', 3), 0.15),
        'gpu_numeric': star_to_weight.get(ai_weights.get('gpu', 3), 0.15)
    }

    # Normalize to sum = 1
    total = sum(raw_weights.values())
    normalized_weights = {k: v / total for k, v in raw_weights.items()}

    return normalized_weights


def test_api_connection() -> tuple[bool, str]:
    """
    Test if ApiFreeLLM is accessible

    Returns:
        tuple of (is_connected, message)
    """
    try:
        result = call_free_llm("Halo, test koneksi. Jawab dengan 'OK'.")
        if result["success"]:
            return True, "Koneksi ke AI berhasil!"
        else:
            return False, result["error"]
    except Exception as e:
        return False, str(e)
