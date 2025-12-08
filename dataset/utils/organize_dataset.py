import os
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading


def organize_dataset(folder_path, progress_callback=None):
    folder = Path(folder_path)
    
    if not folder.exists():
        return False, f"pasta nao encontrada: {folder_path}"
    
    images_dir = folder / "images"
    labels_dir = folder / "labels"
    
    images_dir.mkdir(exist_ok=True)
    labels_dir.mkdir(exist_ok=True)
    
    jpg_files = list(folder.glob("*.jpg"))
    
    if not jpg_files:
        return False, "nenhuma imagem .jpg encontrada na pasta raiz"
    
    moved_count = 0
    ignored_count = 0
    
    for idx, jpg_file in enumerate(jpg_files):
        txt_file = jpg_file.with_suffix('.txt')
        
        if txt_file.exists():
            try:
                shutil.move(str(jpg_file), str(images_dir / jpg_file.name))
                shutil.move(str(txt_file), str(labels_dir / txt_file.name))
                moved_count += 1
                
                if progress_callback:
                    progress = (idx + 1) / len(jpg_files) * 100
                    progress_callback(progress, f"movido: {jpg_file.name}")
            except Exception as e:
                if progress_callback:
                    progress_callback(None, f"erro ao mover {jpg_file.name}: {str(e)}")
        else:
            ignored_count += 1
            if progress_callback:
                progress = (idx + 1) / len(jpg_files) * 100
                progress_callback(progress, f"ignorado (sem .txt): {jpg_file.name}")
    
    return True, {
        'moved': moved_count,
        'ignored': ignored_count,
        'images_dir': str(images_dir),
        'labels_dir': str(labels_dir)
    }


class DatasetOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("organizar dataset - images/labels")
        self.root.geometry("600x400")
        
        self.folder_path = tk.StringVar()
        self.is_processing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="selecionar pasta (ex: dataset/all-images/Gamba):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="procurar", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        
        info_frame = ttk.LabelFrame(main_frame, text="o que o script faz:", padding="10")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(info_frame, text="1. cria pastas 'images' e 'labels' dentro da pasta selecionada").pack(anchor=tk.W)
        ttk.Label(info_frame, text="2. move .jpg para 'images' e .txt para 'labels' (apenas pares correspondentes)").pack(anchor=tk.W)
        ttk.Label(info_frame, text="3. imagens sem .txt ficam na pasta raiz e sao ignoradas").pack(anchor=tk.W)
        
        self.process_button = ttk.Button(main_frame, text="organizar", command=self.start_processing)
        self.process_button.grid(row=3, column=0, pady=10)
        
        ttk.Label(main_frame, text="progresso:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(main_frame, text="aguardando...", foreground="blue")
        self.status_label.grid(row=6, column=0, sticky=tk.W, pady=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="log", padding="5")
        log_frame.grid(row=7, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, width=70)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="selecionar pasta com dataset")
        if folder:
            self.folder_path.set(folder)
            self.log_message(f"pasta selecionada: {folder}")
    
    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, value, status):
        if value is not None:
            self.progress_bar['value'] = value
        if status:
            self.status_label.config(text=status)
        self.root.update_idletasks()
    
    def start_processing(self):
        if self.is_processing:
            messagebox.showwarning("aviso", "processamento ja em andamento")
            return
        
        folder = self.folder_path.get()
        
        if not folder:
            messagebox.showerror("erro", "selecione uma pasta primeiro")
            return
        
        response = messagebox.askyesno(
            "confirmar", 
            "os arquivos serao MOVIDOS (nao copiados).\ncontinuar?"
        )
        
        if not response:
            return
        
        self.is_processing = True
        self.process_button.config(state='disabled')
        self.progress_bar['value'] = 0
        self.log_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.process_folder, args=(folder,))
        thread.start()
    
    def process_folder(self, folder_path):
        try:
            self.log_message("iniciando organizacao do dataset...")
            self.update_progress(0, "processando...")
            
            success, result = organize_dataset(
                folder_path, 
                progress_callback=self.update_progress
            )
            
            if not success:
                self.log_message(f"erro: {result}")
                messagebox.showerror("erro", result)
                return
            
            self.log_message(f"\norganizacao concluida!")
            self.log_message(f"pares movidos: {result['moved']}")
            self.log_message(f"arquivos ignorados (sem correspondencia): {result['ignored']}")
            self.log_message(f"\npasta images: {result['images_dir']}")
            self.log_message(f"pasta labels: {result['labels_dir']}")
            
            self.update_progress(100, "concluido com sucesso")
            
            messagebox.showinfo(
                "concluido", 
                f"dataset organizado com sucesso!\n\n"
                f"pares movidos: {result['moved']}\n"
                f"arquivos ignorados: {result['ignored']}"
            )
            
        except Exception as e:
            self.log_message(f"\nerro durante processamento: {str(e)}")
            messagebox.showerror("erro", f"erro durante processamento:\n{str(e)}")
        
        finally:
            self.is_processing = False
            self.process_button.config(state='normal')


def main():
    root = tk.Tk()
    app = DatasetOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
