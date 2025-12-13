"""
AI Assistant Module for Laptop Recommendation
Advanced Version dengan:
- Dataset Insight
- Session Memory
- Guardrail Prompt
- Klarifikasi Otomatis
- Explainability
"""

import requests
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any


# API Configuration
API_URL = "https://apifreellm.com/api/chat"
TIMEOUT = 60  # seconds


# ============================================================
# CONVERSATION MEMORY CLASS
# ============================================================
class ConversationMemory:
    """
    Menyimpan konteks percakapan dalam sesi.
    Reset jika user refresh halaman.
    """
    def __init__(self):
        self.messages: List[Dict] = []  # [{role, content, timestamp}]
        self.user_preferences: Dict = {}  # {budget, use_case, priorities}
        self.recommended_laptops: List[str] = []  # History nama laptop yang direkomendasikan
        self.clarifications_asked: List[str] = []  # Klarifikasi yang sudah ditanya

    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def update_preferences(self, new_prefs: Dict):
        """Update user preferences"""
        self.user_preferences.update(new_prefs)

    def add_recommended_laptop(self, laptop_name: str):
        """Track recommended laptops"""
        if laptop_name not in self.recommended_laptops:
            self.recommended_laptops.append(laptop_name)

    def mark_clarification_asked(self, topic: str):
        """Mark a clarification topic as asked"""
        if topic not in self.clarifications_asked:
            self.clarifications_asked.append(topic)

    def should_ask_clarification(self, topic: str) -> bool:
        """Check if we should ask for this clarification"""
        return topic not in self.clarifications_asked

    def get_context_summary(self) -> str:
        """Generate context summary for AI prompt"""
        if not self.messages and not self.user_preferences:
            return ""

        summary = "\nKONTEKS PERCAKAPAN SEBELUMNYA:\n"

        if self.user_preferences:
            prefs = []
            if self.user_preferences.get('budget'):
                budget = self.user_preferences['budget']
                prefs.append(f"Budget: Rp {budget:,.0f}".replace(",", "."))
            if self.user_preferences.get('use_case'):
                prefs.append(f"Kebutuhan: {self.user_preferences['use_case']}")
            if prefs:
                summary += f"- Preferensi user: {', '.join(prefs)}\n"

        if self.recommended_laptops:
            summary += f"- Laptop sudah direkomendasikan: {', '.join(self.recommended_laptops[-3:])}\n"

        # Include last 2 messages for context
        if len(self.messages) >= 2:
            summary += "- Percakapan terakhir:\n"
            for msg in self.messages[-2:]:
                role_label = "User" if msg['role'] == 'user' else "AI"
                content_short = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                summary += f"  [{role_label}]: {content_short}\n"

        return summary

    def clear(self):
        """Clear all memory"""
        self.messages = []
        self.user_preferences = {}
        self.recommended_laptops = []
        self.clarifications_asked = []


# ============================================================
# GUARDRAIL PROMPT
# ============================================================
def get_guardrail_prompt(price_min: int, price_max: int) -> str:
    """Generate guardrail rules for AI"""
    return f"""
GUARDRAILS (WAJIB DIIKUTI):

1. BATASAN DATA:
   - HANYA rekomendasikan laptop yang ADA di dataset
   - Jangan membuat spesifikasi atau harga fiktif
   - Jika budget user di luar range dataset, JELASKAN dengan jujur

2. BATASAN RESPONS:
   - Jawab dalam Bahasa Indonesia yang gaul, genz dan ramah
   - Jangan memberikan opini subjektif tentang brand tertentu
   - Fokus pada fakta spesifikasi dan kecocokan kebutuhan

3. BATASAN KEAMANAN:
   - Jangan membahas topik di luar rekomendasi laptop
   - Jangan memberikan saran finansial/kredit
   - Jika pertanyaan off-topic, redirect dengan sopan

4. VALIDASI INPUT:
   - Budget minimum dalam dataset: Rp {price_min:,}
   - Budget maksimum dalam dataset: Rp {price_max:,}
   - Jika budget di luar range, informasikan user

5. KONFLIK HANDLING:
   - Jika kebutuhan bertentangan (gaming + ringan + murah), jelaskan trade-off
   - Berikan alternatif yang realistis
   - Jangan menjanjikan yang tidak mungkin
""".replace(",", ".")


# ============================================================
# DATASET INSIGHT
# ============================================================
def generate_dataset_insight(data_stats: dict, df=None) -> str:
    """
    Generate rich dataset insight untuk konteks AI.
    Memberikan statistik dan informasi berguna tentang dataset.
    """
    price_min_idr = int(data_stats['price']['min'] * 192)
    price_max_idr = int(data_stats['price']['max'] * 192)

    # Calculate average price
    price_avg_idr = (price_min_idr + price_max_idr) // 2

    # RAM distribution
    ram_options = data_stats['ram']['options']
    ram_str = ', '.join([f'{x}GB' for x in ram_options])

    # SSD distribution
    ssd_options = data_stats['ssd']['options']
    ssd_str = ', '.join([f'{x}GB' for x in ssd_options])

    # GPU info
    gpu_options = data_stats['gpu']['options']
    gpu_dedicated = [g for g in gpu_options if g > 0]
    gpu_dedicated_str = ', '.join([f'{x}GB' for x in gpu_dedicated]) if gpu_dedicated else "Tidak ada"

    insight = f"""
INSIGHT DATASET LAPTOP:
- Range Harga: Rp {price_min_idr:,} - Rp {price_max_idr:,} (Rata-rata: ~Rp {price_avg_idr:,})
- Opsi RAM: {ram_str}
- Opsi SSD: {ssd_str}
- Display: {data_stats['display']['min']:.1f}" - {data_stats['display']['max']:.1f}"
- Rating: {data_stats['rating']['min']:.0f} - {data_stats['rating']['max']:.0f}
- GPU Dedicated tersedia: {gpu_dedicated_str}
- GPU Integrated: Ya (VRAM 0GB)

KATEGORI HARGA:
- Budget (< Rp 10 juta): Cocok untuk office/kuliah
- Mid-range (Rp 10-20 juta): Cocok untuk coding/editing ringan
- High-end (> Rp 20 juta): Cocok untuk gaming/editing berat
""".replace(",", ".")

    return insight


# ============================================================
# KLARIFIKASI OTOMATIS
# ============================================================
def check_needs_clarification(message: str, memory: ConversationMemory) -> dict:
    """
    Check if AI needs to ask clarification before processing.
    Returns dict with needed, questions, and missing_info.
    """
    needs_clarification = {
        "needed": False,
        "questions": [],
        "missing_info": []
    }

    message_lower = message.lower()

    # Check if budget is clear
    has_explicit_budget = bool(re.search(r'\d+\s*(juta|jt|ribu|rb|million|m\b)', message_lower))
    budget_vague_keywords = ['murah', 'mahal', 'terjangkau', 'budget', 'hemat', 'ekonomis']
    has_vague_budget = any(word in message_lower for word in budget_vague_keywords) and not has_explicit_budget

    # Also check if budget already known from memory
    budget_known = bool(memory.user_preferences.get('budget'))

    if has_vague_budget and not budget_known and memory.should_ask_clarification('budget'):
        needs_clarification["needed"] = True
        needs_clarification["questions"].append(
            "Berapa budget yang Anda siapkan untuk laptop ini? (dalam jutaan rupiah, misal: 10 juta)"
        )
        needs_clarification["missing_info"].append("budget")

    # Check if use case is clear
    use_case_keywords = ['gaming', 'game', 'editing', 'edit', 'video', 'render',
                         'coding', 'programming', 'ngoding', 'office', 'kantor',
                         'kuliah', 'mahasiswa', 'pelajar', 'kerja', 'desain', 'design']
    has_use_case = any(word in message_lower for word in use_case_keywords)

    vague_request_keywords = ['bagus', 'recommended', 'terbaik', 'worth it', 'rekomen',
                              'suggest', 'saran', 'pilih', 'cari', 'butuh laptop']
    has_vague_request = any(word in message_lower for word in vague_request_keywords) and not has_use_case

    # Also check if use_case already known from memory
    use_case_known = bool(memory.user_preferences.get('use_case'))

    if has_vague_request and not use_case_known and memory.should_ask_clarification('use_case'):
        needs_clarification["needed"] = True
        needs_clarification["questions"].append(
            "Laptop ini akan digunakan untuk apa? (contoh: gaming, editing video, coding, office, kuliah)"
        )
        needs_clarification["missing_info"].append("use_case")

    return needs_clarification


def generate_clarification_response(clarification: dict) -> str:
    """Generate friendly clarification message"""
    questions = clarification["questions"]

    if len(questions) == 1:
        return f"Untuk memberikan rekomendasi yang tepat, saya perlu tahu: {questions[0]}"
    else:
        questions_formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        return f"Untuk memberikan rekomendasi yang tepat, saya perlu beberapa informasi:\n{questions_formatted}"


# ============================================================
# EXPLAINABILITY
# ============================================================
def generate_explanation(laptop: dict, user_prefs: dict, all_candidates: list, rank: int = 1) -> str:
    """
    Generate detailed explanation for why a laptop is recommended.
    Includes criteria match, trade-offs, and comparison.
    """
    explanation = {
        "why_recommended": [],
        "criteria_match": {},
        "trade_offs": [],
        "alternatives": []
    }

    use_case = user_prefs.get('use_case', '').lower()
    budget = user_prefs.get('budget', 0)

    # Price analysis
    laptop_price = laptop.get('price_numeric', 0) * 192  # Convert to IDR
    if budget > 0:
        price_ratio = laptop_price / budget
        if price_ratio <= 0.8:
            explanation["why_recommended"].append(f"💰 Harga Rp {laptop_price/1000000:.1f} Juta - hemat {(1-price_ratio)*100:.0f}% dari budget")
        elif price_ratio <= 1.0:
            explanation["why_recommended"].append(f"💰 Harga Rp {laptop_price/1000000:.1f} Juta - sesuai budget")
        else:
            explanation["trade_offs"].append(f"⚠️ Harga Rp {laptop_price/1000000:.1f} Juta - sedikit melebihi budget")

    # RAM analysis
    ram = laptop.get('ram_numeric', 0)
    if 'gaming' in use_case or 'editing' in use_case or 'coding' in use_case:
        if ram >= 16:
            explanation["why_recommended"].append(f"✅ RAM {ram}GB - optimal untuk {use_case}")
            explanation["criteria_match"]["ram"] = "excellent"
        elif ram >= 8:
            explanation["trade_offs"].append(f"⚠️ RAM {ram}GB - cukup, tapi 16GB lebih ideal untuk {use_case}")
            explanation["criteria_match"]["ram"] = "adequate"
    else:
        if ram >= 8:
            explanation["why_recommended"].append(f"✅ RAM {ram}GB - cukup untuk kebutuhan sehari-hari")

    # GPU analysis
    gpu = laptop.get('gpu_numeric', 0)
    if 'gaming' in use_case or 'editing' in use_case or 'render' in use_case or 'desain' in use_case:
        if gpu >= 6:
            explanation["why_recommended"].append(f"✅ GPU {gpu}GB VRAM - sangat baik untuk {use_case}")
            explanation["criteria_match"]["gpu"] = "excellent"
        elif gpu >= 4:
            explanation["why_recommended"].append(f"✅ GPU {gpu}GB VRAM - cukup baik untuk {use_case}")
            explanation["criteria_match"]["gpu"] = "good"
        elif gpu > 0:
            explanation["trade_offs"].append(f"⚠️ GPU {gpu}GB VRAM - minimal untuk {use_case}, pertimbangkan GPU lebih kuat")
        else:
            explanation["trade_offs"].append(f"⚠️ GPU Integrated - kurang ideal untuk {use_case}")
    elif gpu > 0:
        explanation["why_recommended"].append(f"✅ GPU dedicated {gpu}GB - bonus untuk multitasking")

    # SSD analysis
    ssd = laptop.get('ssd_numeric', 0)
    if ssd >= 512:
        explanation["why_recommended"].append(f"✅ SSD {ssd}GB - kapasitas lega")
    elif ssd >= 256:
        explanation["trade_offs"].append(f"⚠️ SSD {ssd}GB - cukup, tapi mungkin perlu storage eksternal")

    # Rating analysis
    rating = laptop.get('rating_numeric', 0) or laptop.get('Rating', 0)
    if rating >= 80:
        explanation["why_recommended"].append(f"⭐ Rating {rating}/100 - sangat direkomendasikan user lain")
    elif rating >= 60:
        explanation["why_recommended"].append(f"⭐ Rating {rating}/100 - ulasan cukup baik")

    # Find alternatives
    if len(all_candidates) > 1 and rank == 1:
        # Find cheaper alternative
        cheaper = [l for l in all_candidates if l.get('price_numeric', 0) < laptop.get('price_numeric', 0)]
        if cheaper:
            cheapest = min(cheaper, key=lambda x: x.get('price_numeric', 0))
            cheap_price = cheapest.get('price_numeric', 0) * 192
            explanation["alternatives"].append(
                f"💡 Alternatif lebih hemat: {cheapest.get('Model', 'N/A')[:30]} (Rp {cheap_price/1000000:.1f} Juta)"
            )

        # Find better spec alternative
        better_gpu = [l for l in all_candidates if l.get('gpu_numeric', 0) > laptop.get('gpu_numeric', 0)]
        if better_gpu and ('gaming' in use_case or 'editing' in use_case):
            best_gpu = max(better_gpu, key=lambda x: x.get('gpu_numeric', 0))
            explanation["alternatives"].append(
                f"💡 Alternatif GPU lebih kuat: {best_gpu.get('Model', 'N/A')[:30]} (GPU {best_gpu.get('gpu_numeric', 0)}GB)"
            )

    return format_explanation(explanation)


def format_explanation(exp: dict) -> str:
    """Format explanation dict to readable string"""
    parts = []

    if exp["why_recommended"]:
        parts.append("**Kelebihan:**")
        for reason in exp["why_recommended"]:
            parts.append(f"  {reason}")

    if exp["trade_offs"]:
        parts.append("\n**Pertimbangan:**")
        for tradeoff in exp["trade_offs"]:
            parts.append(f"  {tradeoff}")

    if exp["alternatives"]:
        parts.append("\n**Alternatif:**")
        for alt in exp["alternatives"]:
            parts.append(f"  {alt}")

    return "\n".join(parts) if parts else ""


# ============================================================
# SYSTEM PROMPT (UPDATED)
# ============================================================
def build_system_prompt(data_stats: dict, memory: ConversationMemory) -> str:
    """Build complete system prompt with all components"""

    price_min_idr = int(data_stats['price']['min'] * 192)
    price_max_idr = int(data_stats['price']['max'] * 192)

    guardrails = get_guardrail_prompt(price_min_idr, price_max_idr)
    dataset_insight = generate_dataset_insight(data_stats)
    conversation_context = memory.get_context_summary()

    return f"""Kamu adalah asisten AI untuk merekomendasikan laptop. Tugasmu adalah:
1. Memahami kebutuhan user dari chat mereka
2. Jika informasi kurang, minta klarifikasi
3. Menentukan filter dan bobot prioritas untuk pencarian laptop
4. Memberikan penjelasan mengapa rekomendasi cocok

{guardrails}

{dataset_insight}

{conversation_context}

KRITERIA PENILAIAN:
- price: Harga laptop (COST - semakin murah semakin baik)
- ram: Kapasitas RAM dalam GB (BENEFIT - semakin besar semakin baik)
- ssd: Kapasitas storage dalam GB (BENEFIT - semakin besar semakin baik)
- rating: Rating laptop 0-100 (BENEFIT - semakin tinggi semakin baik)
- display: Ukuran layar dalam inch (BENEFIT - semakin besar semakin baik)
- gpu: VRAM GPU dalam GB, 0 = integrated (BENEFIT - semakin besar semakin baik)

MAPPING KEBUTUHAN:
- Gaming/Game: GPU tinggi (>=4GB), RAM tinggi (>=16GB), Display besar
- Editing Video/Render/3D: GPU sangat tinggi, RAM sangat tinggi (>=16GB), SSD besar
- Programming/Coding: RAM tinggi, SSD cepat, Display sedang-besar
- Office/Kerja Kantor: RAM sedang (8GB cukup), SSD sedang, Harga terjangkau
- Kuliah/Mahasiswa/Pelajar: Harga murah, RAM cukup, portabel (display kecil-sedang)
- Desain Grafis: GPU dedicated, RAM tinggi, Display bagus

FORMAT RESPONSE (JSON):
{{
  "needs_clarification": true/false,
  "clarification_questions": ["pertanyaan 1", "pertanyaan 2"] atau [],
  "understood": true/false,
  "use_case": "deskripsi singkat kebutuhan",
  "response_message": "pesan balasan untuk user dalam Bahasa Indonesia yang heboh dan gaul",
  "filters": {{
    "price_max": angka dalam rupiah atau null,
    "price_min": angka dalam rupiah atau null,
    "ram_min": angka GB atau null,
    "ssd_min": angka GB atau null,
    "gpu_min": angka GB atau null,
    "rating_min": angka 0-100 atau null
  }},
  "weights": {{
    "price": angka 1-5,
    "ram": angka 1-5,
    "ssd": angka 1-5,
    "rating": angka 1-5,
    "display": angka 1-5,
    "gpu": angka 1-5
  }},
  "detected_preferences": {{
    "budget": angka atau null,
    "use_case": "gaming/editing/coding/office/kuliah" atau null
  }}
}}

PENTING:
- Semua angka harga dalam RUPIAH (bukan juta, tulis lengkap misal 15000000)
- Bobot 1-5 dimana 5 = sangat penting, 1 = tidak penting
- Jika user tidak menyebut kriteria tertentu, gunakan nilai default atau null
- response_message harus ramah dan informatif
- SELALU kembalikan JSON yang valid
"""


# ============================================================
# MAIN FUNCTIONS
# ============================================================
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
            if isinstance(data, dict):
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


def parse_user_message(message: str, data_stats: dict, memory: ConversationMemory = None) -> dict:
    """
    Parse user message using ApiFreeLLM and return filters + weights.
    Now includes clarification check and memory context.

    Returns:
        dict with keys: success, response_message, filters, weights, needs_clarification, etc.
    """
    if memory is None:
        memory = ConversationMemory()

    result = {
        "success": False,
        "response_message": "",
        "filters": {},
        "weights": {},
        "needs_clarification": False,
        "clarification_questions": [],
        "detected_preferences": {},
        "error": None
    }

    # First, check if we need clarification (local check)
    clarification = check_needs_clarification(message, memory)
    if clarification["needed"]:
        result["needs_clarification"] = True
        result["clarification_questions"] = clarification["questions"]
        result["response_message"] = generate_clarification_response(clarification)
        # Mark these topics as asked
        for topic in clarification["missing_info"]:
            memory.mark_clarification_asked(topic)
        return result

    # Build the full prompt with all context
    system_prompt = build_system_prompt(data_stats, memory)
    full_prompt = system_prompt + f"\n\nUser: {message}\n\nResponse (JSON only):"

    # Call the API
    api_result = call_free_llm(full_prompt)

    if not api_result["success"]:
        result["error"] = api_result["error"]
        result["response_message"] = f"Maaf, terjadi kesalahan: {api_result['error']}"
        # Fallback to simple parsing
        return parse_simple_fallback(message, data_stats, "", memory)

    response_text = api_result["response"]

    # Try to extract JSON from response
    try:
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            parsed = json.loads(json_str)

            # Check if AI wants clarification
            if parsed.get("needs_clarification", False):
                result["needs_clarification"] = True
                result["clarification_questions"] = parsed.get("clarification_questions", [])
                result["response_message"] = parsed.get("response_message",
                    generate_clarification_response({"questions": result["clarification_questions"]}))
                return result

            if parsed.get("understood", True):
                result["success"] = True
                result["response_message"] = parsed.get("response_message", "Saya sudah menganalisis kebutuhan Anda.")
                result["filters"] = parsed.get("filters", {})
                result["weights"] = parsed.get("weights", {
                    "price": 3, "ram": 3, "ssd": 3,
                    "rating": 3, "display": 3, "gpu": 3
                })
                result["use_case"] = parsed.get("use_case", "")
                result["detected_preferences"] = parsed.get("detected_preferences", {})

                # Update memory with detected preferences
                if result["detected_preferences"]:
                    memory.update_preferences(result["detected_preferences"])
            else:
                result["success"] = False
                result["response_message"] = parsed.get("response_message",
                    "Maaf, saya kurang memahami kebutuhan Anda. Bisa dijelaskan lebih detail?")
        else:
            result = parse_simple_fallback(message, data_stats, response_text, memory)

    except json.JSONDecodeError:
        result = parse_simple_fallback(message, data_stats, response_text, memory)
    except Exception as e:
        result["error"] = str(e)
        result["response_message"] = "Maaf, terjadi kesalahan dalam memproses permintaan."

    return result


def parse_simple_fallback(message: str, data_stats: dict, ai_response: str = "", memory: ConversationMemory = None) -> dict:
    """
    Simple fallback parser when AI doesn't return proper JSON.
    Uses keyword matching to determine filters and weights.
    """
    message_lower = message.lower()

    # Default weights
    weights = {
        "price": 3, "ram": 3, "ssd": 3,
        "rating": 3, "display": 3, "gpu": 3
    }

    filters = {}
    detected_preferences = {}
    use_case = ""

    # Parse budget
    budget_match = re.search(r'(\d+)\s*(juta|jt|million|m\b)', message_lower)
    if budget_match:
        budget = int(budget_match.group(1)) * 1000000
        filters["price_max"] = budget
        detected_preferences["budget"] = budget

    # Parse use case and set weights
    if any(word in message_lower for word in ['gaming', 'game', 'main game']):
        weights = {"price": 2, "ram": 4, "ssd": 3, "rating": 3, "display": 4, "gpu": 5}
        filters["gpu_min"] = 4
        filters["ram_min"] = 16
        use_case = "gaming"
        detected_preferences["use_case"] = "gaming"

    elif any(word in message_lower for word in ['editing', 'edit', 'video', 'render', '3d', 'desain']):
        weights = {"price": 2, "ram": 5, "ssd": 4, "rating": 3, "display": 4, "gpu": 5}
        filters["gpu_min"] = 4
        filters["ram_min"] = 16
        filters["ssd_min"] = 512
        use_case = "editing"
        detected_preferences["use_case"] = "editing"

    elif any(word in message_lower for word in ['programming', 'coding', 'developer', 'programmer', 'ngoding']):
        weights = {"price": 3, "ram": 5, "ssd": 4, "rating": 3, "display": 4, "gpu": 2}
        filters["ram_min"] = 16
        filters["ssd_min"] = 512
        use_case = "coding"
        detected_preferences["use_case"] = "coding"

    elif any(word in message_lower for word in ['office', 'kantor', 'kerja', 'bisnis']):
        weights = {"price": 4, "ram": 3, "ssd": 3, "rating": 4, "display": 3, "gpu": 1}
        filters["ram_min"] = 8
        use_case = "office"
        detected_preferences["use_case"] = "office"

    elif any(word in message_lower for word in ['kuliah', 'mahasiswa', 'pelajar', 'sekolah', 'student']):
        weights = {"price": 5, "ram": 3, "ssd": 3, "rating": 3, "display": 2, "gpu": 1}
        filters["ram_min"] = 8
        use_case = "kuliah"
        detected_preferences["use_case"] = "kuliah"

    elif any(word in message_lower for word in ['murah', 'budget', 'hemat', 'terjangkau']):
        weights = {"price": 5, "ram": 3, "ssd": 2, "rating": 3, "display": 2, "gpu": 1}

    # Update memory if available
    if memory and detected_preferences:
        memory.update_preferences(detected_preferences)

    # Generate response message
    if ai_response and len(ai_response) > 20:
        response_message = ai_response[:500]
    else:
        response_parts = ["Baik, saya akan carikan laptop"]
        if use_case:
            response_parts.append(f"untuk {use_case}")
        if filters.get("price_max"):
            budget_str = f"Rp {filters['price_max']:,.0f}".replace(",", ".")
            response_parts.append(f"dengan budget maksimal {budget_str}")
        response_message = " ".join(response_parts) + "."

        if filters.get("ram_min"):
            response_message += f" RAM minimal {filters['ram_min']}GB."
        if filters.get("gpu_min"):
            response_message += f" GPU dedicated minimal {filters['gpu_min']}GB."

    return {
        "success": True,
        "response_message": response_message,
        "filters": filters,
        "weights": weights,
        "use_case": use_case,
        "needs_clarification": False,
        "clarification_questions": [],
        "detected_preferences": detected_preferences,
        "error": None
    }


def convert_ai_filters_to_app_filters(ai_filters: dict, data_stats: dict) -> dict:
    """Convert AI-generated filters to app filter format"""
    price_min_idr = int(data_stats['price']['min'] * 192)
    price_max_idr = int(data_stats['price']['max'] * 192)
    ram_options = data_stats['ram']['options']
    ssd_options = data_stats['ssd']['options']
    gpu_options = data_stats['gpu']['options']

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
    """Convert AI star ratings (1-5) to normalized weights for SAW"""
    star_to_weight = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20, 5: 0.25}

    raw_weights = {
        'price_numeric': star_to_weight.get(ai_weights.get('price', 3), 0.15),
        'ram_numeric': star_to_weight.get(ai_weights.get('ram', 3), 0.15),
        'ssd_numeric': star_to_weight.get(ai_weights.get('ssd', 3), 0.15),
        'rating_numeric': star_to_weight.get(ai_weights.get('rating', 3), 0.15),
        'display_numeric': star_to_weight.get(ai_weights.get('display', 3), 0.15),
        'gpu_numeric': star_to_weight.get(ai_weights.get('gpu', 3), 0.15)
    }

    total = sum(raw_weights.values())
    normalized_weights = {k: v / total for k, v in raw_weights.items()}

    return normalized_weights


def test_api_connection() -> tuple:
    """Test if ApiFreeLLM is accessible"""
    try:
        result = call_free_llm("Halo, test koneksi. Jawab dengan 'OK'.")
        if result["success"]:
            return True, "Koneksi ke AI berhasil!"
        else:
            return False, result["error"]
    except Exception as e:
        return False, str(e)
