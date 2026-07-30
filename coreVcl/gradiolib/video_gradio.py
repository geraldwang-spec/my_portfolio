import gradio as gr
from gradiolib.module_process import translate_module as tm

def create_and_launch_gradio(server_name="0.0.0.0", server_port=7860, share=False)->None:
    
    translator = tm(path="./saved_model")
    model_loaded = translator.load_model()

    def greet(name:str )->str:
        return f"Hello, {name}!"

    def gradio_translate(text:str)->str:
        if not model_loaded:
            return "load model fail"
        
        try:
            return translator.translate(text)
        except Exception as e:
            return f"translator fail {e}"


    gui = gr.Interface(
        fn = gradio_translate,
        inputs=gr.Textbox(label="請輸入中文", lines=3),
        outputs = gr.Textbox(label="翻譯英文", lines=3),
        title="奇怪翻譯機"
    )

    gui.launch(
        server_name=server_name,
        server_port = server_port,
        root_path="/gradio",
        share=share,
        prevent_thread_lock=True,
    )
