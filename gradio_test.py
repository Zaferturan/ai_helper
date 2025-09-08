import gradio as gr
import requests
import json
import os

# Backend URL
BACKEND_URL = "http://localhost:8000/api/v1"

def copy_to_clipboard(text):
    """JavaScript ile clipboard kopyalama"""
    return f"""
    <script>
    navigator.clipboard.writeText(`{text}`).then(() => {{
        console.log('Copied to clipboard');
        // Başarı mesajı göster
        document.getElementById('copy-status').innerHTML = '✅ Kopyalandı!';
        setTimeout(() => {{
            document.getElementById('copy-status').innerHTML = '';
        }}, 2000);
    }}).catch(err => {{
        console.error('Copy failed:', err);
        document.getElementById('copy-status').innerHTML = '❌ Kopyalama başarısız';
    }});
    </script>
    <div id="copy-status"></div>
    """

def generate_response(original_text, custom_input, temperature=0.5, top_p=0.4, repetition_penalty=2.0):
    """Backend API'ye request gönder"""
    try:
        # Request oluştur
        request_data = {
            "original_text": original_text,
            "is_new_request": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/requests/",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            request_id = response.json().get("id")
            
            # Yanıt üret
            response_data = {
                "request_id": request_id,
                "custom_input": custom_input,
                "temperature": temperature,
                "top_p": top_p,
                "repetition_penalty": repetition_penalty,
                "model_name": "gemini-2.5-flash"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/generate",
                json=response_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response_text", "Yanıt üretilemedi"), True
            else:
                return f"❌ Yanıt üretilemedi: {response.status_code}", False
        else:
            return f"❌ Request oluşturulamadı: {response.status_code}", False
            
    except Exception as e:
        return f"❌ Hata: {str(e)}", False

def test_backend():
    """Backend bağlantısını test et"""
    try:
        response = requests.get(f"{BACKEND_URL}/auth/health", timeout=10)
        if response.status_code == 200:
            return "✅ Backend bağlantısı başarılı"
        else:
            return f"❌ Backend hatası: {response.status_code}"
    except Exception as e:
        return f"❌ Backend bağlantısı başarısız: {str(e)}"

# Gradio Interface
with gr.Blocks(title="AI Helper - Gradio Test", theme=gr.themes.Soft()) as demo:
    
    # Header
    gr.Markdown("""
    # 🤖 AI Helper - Gradio Test
    ### Clipboard ve Backend API Test Uygulaması
    """)
    
    # Backend test
    with gr.Row():
        test_btn = gr.Button("🔍 Backend Bağlantısını Test Et", variant="secondary")
        test_output = gr.Textbox(label="Test Sonucu", interactive=False)
    
    # Ana form
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Gelen İstek/Öneri")
            original_text = gr.Textbox(
                label="Gelen istek/öneri metnini buraya yapıştırın:",
                value="Bursa Nilüfer'de bir dükkanım var ve yönetim planından tahsisli otoparkımda bulunan dubaları, belediye ekipleri mafyavari şekilde tahsisli alanımdan alıp götürebiliyor. Geri aradığımda ise belediye zabıtası, görevliyi mahkemeye vermemi söylüyor. Bu nasıl bir hizmet anlayışı?",
                lines=5
            )
            
            gr.Markdown("### ✍️ Hazırladığınız Cevap")
            custom_input = gr.Textbox(
                label="Hazırladığınız cevap taslağını buraya yazın:",
                value="Orası size tahsis edilmiş bir yer değil. Nilüfer halkının ortak kullanım alanı. Kaldırımlar da öyle.",
                lines=3
            )
            
            # Ayarlar
            with gr.Accordion("🔧 Yanıt Ayarları", open=False):
                temperature = gr.Slider(
                    minimum=0.0, maximum=2.0, value=0.5, step=0.1,
                    label="🌡️ Temperature",
                    info="Düşük değerler daha tutarlı, yüksek değerler daha yaratıcı yanıtlar üretir"
                )
                top_p = gr.Slider(
                    minimum=0.0, maximum=1.0, value=0.4, step=0.1,
                    label="🎯 Top-p",
                    info="Kelime seçiminde çeşitliliği kontrol eder"
                )
                repetition_penalty = gr.Slider(
                    minimum=0.0, maximum=3.0, value=2.0, step=0.1,
                    label="🔄 Repetition Penalty",
                    info="Tekrarlanan kelimeleri azaltır"
                )
            
            generate_btn = gr.Button("🚀 Yanıt Üret", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            gr.Markdown("### ✅ Son Yanıt")
            response_output = gr.Textbox(
                label="Üretilen yanıt:",
                lines=10,
                interactive=False
            )
            
            with gr.Row():
                copy_btn = gr.Button("📋 Kopyala", variant="secondary")
                clear_btn = gr.Button("🗑️ Temizle", variant="secondary")
            
            gr.Markdown("### 📊 Test Sonuçları")
            status_output = gr.Textbox(
                label="Durum:",
                lines=3,
                interactive=False
            )
    
    # Event handlers
    def on_test_backend():
        return test_backend()
    
    def on_generate(orig, custom, temp, top_p_val, rep_pen):
        response_text, success = generate_response(orig, custom, temp, top_p_val, rep_pen)
        status = "✅ Yanıt başarıyla üretildi!" if success else "❌ Yanıt üretilemedi!"
        return response_text, status
    
    def on_copy(text):
        if text:
            return copy_to_clipboard(text)
        return ""
    
    def on_clear():
        return "", "", ""
    
    # Event connections
    test_btn.click(on_test_backend, outputs=test_output)
    generate_btn.click(
        on_generate,
        inputs=[original_text, custom_input, temperature, top_p, repetition_penalty],
        outputs=[response_output, status_output]
    )
    copy_btn.click(on_copy, inputs=response_output, outputs=gr.HTML())
    clear_btn.click(on_clear, outputs=[original_text, custom_input, response_output])

# Launch
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=8501,
        share=False,
        show_error=True
    )


