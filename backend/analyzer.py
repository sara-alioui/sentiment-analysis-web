import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
import os
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import time
import sys
from ttkthemes import ThemedTk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import random
from tkinter import Canvas
import math


class SentimentAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SAZAfeels - Analyse de Sentiments Twitter")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Configuration des chemins
        self.base_path = Path(r"C:\xampp\htdocs\sentiment-analysis-web")
        self.frontend_path = self.base_path / "frontend"
        self.data_path = self.frontend_path / "data"

        # Variables
        self.status_var = tk.StringVar(value="Prêt")
        self.progress_var = tk.DoubleVar(value=0)
        self.search_term_var = tk.StringVar(value="")
        self.sample_size_var = tk.StringVar(value="100")
        self.csv_path_var = tk.StringVar(value="training.1600000.processed.noemoticon.csv")
        self.theme_var = tk.StringVar(value="blue")

        # Thème bleu ciel amélioré
        self.themes = {
            "blue": {
                "bg": "#E8F4FD",  # Fond bleu ciel plus vif
                "fg": "#1A3A5C",  # Texte bleu plus foncé pour meilleur contraste
                "highlight": "#1E88E5",  # Bleu vif plus moderne
                "accent": "#4CA3D4",  # Bleu medium
                "button": "#2196F3",  # Bleu clair plus vif
                "success": "#4CAF50",  # Vert plus vif
                "warning": "#FFC107",  # Jaune plus vif
                "error": "#F44336",  # Rouge plus vif
                "text_bg": "#FFFFFF",  # Blanc
                "card_bg": "#F5FAFF",  # Bleu très pâle plus chaleureux
                "header_bg": "#1565C0",  # En-tête bleu foncé
                "header_fg": "#FFFFFF"  # Texte d'en-tête blanc
            }
        }

        # Configurer les styles
        self.configure_styles()

        # Charger logo
        self.load_logos()

        # Créer la page de bienvenue
        self.welcome_page = WelcomePage(root, self)

        # Résultats de l'analyse
        self.analysis_results = []

        # Initialiser l'interface principale
        self.main_frame = None
        self.left_panel = None
        self.right_panel = None
        self.run_btn = None
        self.details_tab = None
        self.stats_tab = None
        self.text_details = None
        self.tabs = None

    def create_rounded_button(self, parent, text, command, bg_color, fg_color="white", width=None):
        """Crée un bouton avec des coins arrondis"""
        theme = self.themes["blue"]

        # Créer un canvas qui servira de bouton
        canvas = tk.Canvas(parent,
                           bg=theme["bg"],
                           height=40,
                           width=width if width else 200,
                           highlightthickness=0,
                           relief='ridge')

        # Dessiner le rectangle arrondi
        radius = 20
        canvas.create_rounded_rect(0, 0,
                                   width if width else 200, 40,
                                   radius=radius,
                                   fill=bg_color,
                                   outline=bg_color)  # Suppression de la bordure pour un look plus moderne

        # Ajouter le texte avec une police plus moderne
        canvas.create_text((width // 2 if width else 100), 20,
                           text=text,
                           fill=fg_color,
                           font=("Montserrat", 12, "bold"))

        # Lier l'événement clic
        canvas.bind("<Button-1>", lambda e: command())

        # Effet de survol amélioré
        def on_enter(e):
            # Assombrir légèrement la couleur de fond pour effet de survol
            darker_color = self.darken_color(bg_color)
            canvas.itemconfig(1, fill=darker_color)

        def on_leave(e):
            canvas.itemconfig(1, fill=bg_color)

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)

        return canvas

    def darken_color(self, hex_color, factor=0.85):
        """Assombrit une couleur hexadécimale"""
        # Convertir hex en RGB
        h = hex_color.lstrip('#')
        rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

        # Assombrir
        rgb_dark = tuple(int(c * factor) for c in rgb)

        # Reconvertir en hex
        return '#{:02x}{:02x}{:02x}'.format(rgb_dark[0], rgb_dark[1], rgb_dark[2])

    # Ajouter la méthode create_rounded_rect à la classe Canvas
    Canvas.create_rounded_rect = lambda self, x1, y1, x2, y2, radius=25, **kwargs: self.create_polygon(
        [x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius, x2, y2 - radius, x2, y2, x2 - radius, y2,
         x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1],
        **kwargs, smooth=True)

    def load_logos(self):
        """Charge les logos depuis les fichiers"""
        try:
            # Charger le logo principal
            self.logo_img = Image.open("logo.jpg")
            self.logo = ImageTk.PhotoImage(self.logo_img.resize((180, 180)))

            # Créer une version plus petite pour l'en-tête
            self.small_logo = ImageTk.PhotoImage(self.logo_img.resize((40, 40)))

            print("Logos chargés avec succès")
        except Exception as e:
            print(f"Erreur lors du chargement des logos: {e}")
            # Créer un logo de secours simple
            img = Image.new('RGB', (180, 180), self.themes["blue"]["highlight"])
            draw = ImageDraw.Draw(img)
            draw.text((60, 70), "SAZAfeels", fill='white', font=ImageFont.load_default())
            self.logo = ImageTk.PhotoImage(img)
            self.small_logo = ImageTk.PhotoImage(img.resize((40, 40)))

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Configuration du style bleu amélioré
        style.configure(".", background=self.themes["blue"]["bg"],
                        foreground=self.themes["blue"]["fg"])
        style.configure("TFrame", background=self.themes["blue"]["bg"])
        style.configure("Blue.TFrame", background=self.themes["blue"]["bg"])
        style.configure("TLabel", background=self.themes["blue"]["bg"],
                        foreground=self.themes["blue"]["fg"],
                        font=("Segoe UI", 10))  # Police plus moderne
        style.configure("TButton", background=self.themes["blue"]["button"],
                        foreground="white", borderwidth=0,
                        font=("Segoe UI", 10, "bold"))
        style.map("TButton",
                  background=[('active', self.themes["blue"]["highlight"])],
                  foreground=[('active', 'white')])
        style.configure("TEntry", fieldbackground="white",
                        foreground=self.themes["blue"]["fg"],
                        borderwidth=1, padding=5)
        style.configure("Blue.TEntry", fieldbackground="white",
                        foreground="#333333", padding=5)
        style.configure("TProgressbar", background=self.themes["blue"]["accent"],
                        troughcolor=self.themes["blue"]["text_bg"],
                        thickness=10)  # Barre plus épaisse
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"),
                        background=self.themes["blue"]["bg"],
                        foreground=self.themes["blue"]["highlight"])
        style.configure("Subheader.TLabel", font=("Segoe UI", 14),
                        background=self.themes["blue"]["bg"],
                        foreground=self.themes["blue"]["fg"])
        style.configure("Status.TLabel", background=self.themes["blue"]["card_bg"],
                        foreground=self.themes["blue"]["accent"],
                        font=("Segoe UI", 10))
        style.configure("Card.TFrame", background=self.themes["blue"]["card_bg"],
                        borderwidth=0, relief="flat", padding=10)
        style.configure("Card.TLabel", background=self.themes["blue"]["card_bg"],
                        foreground=self.themes["blue"]["fg"])
        style.configure("TNotebook", background=self.themes["blue"]["bg"],
                        borderwidth=0, padding=5)
        style.configure("TNotebook.Tab", background=self.themes["blue"]["bg"],
                        foreground=self.themes["blue"]["fg"],
                        padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[('selected', self.themes["blue"]["accent"])],
                  foreground=[('selected', 'white')])

    def setup_ui(self):
        self.apply_theme()
        self.create_main_interface()

    def apply_theme(self):
        theme = self.themes["blue"]
        self.root.configure(bg=theme["bg"])

    def create_main_interface(self):
        self.main_frame = ttk.Frame(self.root, style="Blue.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Ajout d'un en-tête principal
        self.create_main_header()

        # Panneau de gauche (contrôles)
        self.left_panel = ttk.Frame(self.main_frame, width=300, style="Blue.TFrame")
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 15))

        # Configuration frame
        self.create_config_frame()

        # Boutons d'action
        self.create_action_buttons()

        # État et progression
        self.create_status_frame()

        # Panneau de droite (visualisations)
        self.right_panel = ttk.Frame(self.main_frame, style="Blue.TFrame")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_visualization_tabs()

    def create_main_header(self):
        """Ajoute un en-tête moderne et épuré avec bouton d'accueil"""
        theme = self.themes["blue"]

        header_frame = tk.Frame(self.root, bg=theme["header_bg"], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # Logo et titre
        try:
            logo_label = tk.Label(header_frame, image=self.small_logo, bg=theme["header_bg"])
            logo_label.pack(side=tk.LEFT, padx=20, pady=10)
        except:
            logo_label = tk.Label(header_frame, text="🧠", font=("Segoe UI", 20),
                                  bg=theme["header_bg"], fg="white")
            logo_label.pack(side=tk.LEFT, padx=20, pady=10)

        title_label = tk.Label(header_frame, text="SAZAfeels", font=("Segoe UI", 18, "bold"),
                               bg=theme["header_bg"], fg="white")
        title_label.pack(side=tk.LEFT, padx=5, pady=10)

        subtitle_label = tk.Label(header_frame, text="Analyse de Sentiments Twitter",
                                  font=("Segoe UI", 12),
                                  bg=theme["header_bg"], fg="#E0E0E0")
        subtitle_label.pack(side=tk.LEFT, padx=5, pady=10)

        # Bouton Accueil côté droit avec style plus visible
        back_btn = tk.Button(header_frame, text="🏠 Accueil", font=("Segoe UI", 12, "bold"),
                             bg=theme["success"], fg="white", bd=0, padx=20, pady=8,
                             relief="raised", command=self.show_welcome_page, cursor="hand2")
        back_btn.pack(side=tk.RIGHT, padx=30, pady=12)

        # Ajoutons un effet de survol pour renforcer la visibilité du bouton
        def on_enter(e):
            back_btn['background'] = self.darken_color(theme["success"])

        def on_leave(e):
            back_btn['background'] = theme["success"]

        back_btn.bind("<Enter>", on_enter)
        back_btn.bind("<Leave>", on_leave)

    def create_config_frame(self):
        config_frame = ttk.LabelFrame(self.left_panel, text="Configuration", style="Card.TFrame")
        config_frame.pack(fill=tk.X, pady=10)

        ttk.Label(config_frame, text="Fichier de données:", style="Card.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 5))

        csv_frame = ttk.Frame(config_frame, style="Card.TFrame")
        csv_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Entry(csv_frame, textvariable=self.csv_path_var, style="Blue.TEntry").pack(side=tk.LEFT, fill=tk.X,
                                                                                       expand=True)

        browse_btn = ttk.Button(csv_frame, text="Parcourir", command=self.browse_csv,
                                style="TButton", width=10)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Label(config_frame, text="Terme à rechercher:", style="Card.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 5))
        ttk.Entry(config_frame, textvariable=self.search_term_var,
                  style="Blue.TEntry").pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(config_frame, text="Taille de l'échantillon:", style="Card.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 5))

        # Utilisation d'un Scale pour la taille de l'échantillon
        sample_frame = ttk.Frame(config_frame, style="Card.TFrame")
        sample_frame.pack(fill=tk.X, padx=5, pady=5)

        scale = ttk.Scale(sample_frame, from_=10, to=1000, length=200,
                          orient=tk.HORIZONTAL,
                          value=int(self.sample_size_var.get()),
                          command=lambda v: self.sample_size_var.set(str(int(float(v)))))
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        value_label = ttk.Label(sample_frame, textvariable=self.sample_size_var,
                                style="Card.TLabel", width=4)
        value_label.pack(side=tk.RIGHT)

    def create_action_buttons(self):
        actions_frame = ttk.LabelFrame(self.left_panel, text="Actions", style="Card.TFrame")
        actions_frame.pack(fill=tk.X, pady=10)

        theme = self.themes["blue"]

        # Bouton "Accueil" au début de la liste
        self.home_btn = self.create_rounded_button(
            actions_frame,
            "🏠 Accueil",
            self.show_welcome_page,
            bg_color=theme["highlight"],  # Couleur distincte
            width=280
        )
        self.home_btn.pack(fill=tk.X, padx=5, pady=10)

        # Bouton "Lancer l'analyse" plus grand
        self.run_btn = self.create_rounded_button(
            actions_frame,
            "🚀 Lancer l'analyse",
            self.run_analysis,
            bg_color=theme["success"],
            width=280
        )
        self.run_btn.pack(fill=tk.X, padx=5, pady=10)

        # Bouton "Voir dans le navigateur"
        self.view_btn = self.create_rounded_button(
            actions_frame,
            "🌐 Voir dans le navigateur",
            self.open_web_interface,
            bg_color=theme["accent"],
            width=280
        )
        self.view_btn.pack(fill=tk.X, padx=5, pady=5)

        # Bouton "Ouvrir le dossier"
        self.folder_btn = self.create_rounded_button(
            actions_frame,
            "📁 Ouvrir le dossier",
            self.open_results_folder,
            bg_color=theme["accent"],
            width=280
        )
        self.folder_btn.pack(fill=tk.X, padx=5, pady=5)

        # Bouton "Exporter les résultats"
        self.export_btn = self.create_rounded_button(
            actions_frame,
            "💾 Exporter les résultats",
            self.export_results,
            bg_color=theme["button"],
            fg_color="white",
            width=280
        )
        self.export_btn.pack(fill=tk.X, padx=5, pady=5)

    def create_status_frame(self):
        status_frame = ttk.LabelFrame(self.left_panel, text="État", style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=10)

        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                 style="Status.TLabel", font=("Segoe UI", 11))
        status_label.pack(anchor=tk.W, padx=5, pady=5)

        progress_frame = ttk.Frame(status_frame, style="Card.TFrame")
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        # Barre de progression améliorée
        ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100,
                        mode='determinate', length=280,
                        style="TProgressbar").pack(fill=tk.X, pady=5)

        # Indicateur de pourcentage
        percentage_label = ttk.Label(progress_frame, text="0%", style="Card.TLabel")
        percentage_label.pack(anchor=tk.E, padx=5)

        # Mise à jour du pourcentage
        def update_percentage(*args):
            percentage_label.config(text=f"{int(self.progress_var.get())}%")

        self.progress_var.trace_add("write", update_percentage)

    def create_visualization_tabs(self):
        self.tabs = ttk.Notebook(self.right_panel)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.details_tab = ttk.Frame(self.tabs, style="Blue.TFrame")
        self.tabs.add(self.details_tab, text="📋 Détails")

        self.details_frame = ttk.Frame(self.details_tab, style="Blue.TFrame")
        self.details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        theme = self.themes["blue"]

        # Texte avec fond blanc et bordure légère
        text_frame = ttk.Frame(self.details_frame, style="Card.TFrame")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.text_details = tk.Text(text_frame, wrap=tk.WORD,
                                    bg=theme["text_bg"], fg=theme["fg"],
                                    font=("Segoe UI", 11), padx=15, pady=15,
                                    relief="flat", borderwidth=0)
        self.text_details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=self.text_details.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_details.config(yscrollcommand=scrollbar.set)

        # Message initial plus attrayant
        self.text_details.insert(tk.END, "Lancez l'analyse pour voir les résultats détaillés.\n\n")
        self.text_details.insert(tk.END, "Les résultats afficheront les tweets analysés avec leur score de sentiment.")
        self.text_details.config(state=tk.DISABLED)

        self.stats_tab = ttk.Frame(self.tabs, style="Blue.TFrame")
        self.tabs.add(self.stats_tab, text="📊 Statistiques")

        # Message d'invite plus centré et visible
        stats_placeholder_frame = ttk.Frame(self.stats_tab, style="Card.TFrame")
        stats_placeholder_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ttk.Label(stats_placeholder_frame, text="📊",
                  font=("Segoe UI", 48)).pack(pady=(0, 10))

        ttk.Label(stats_placeholder_frame, text="Statistiques disponibles après analyse",
                  style="Subheader.TLabel").pack()

    def show_welcome_page(self):
        if self.main_frame:
            self.main_frame.pack_forget()
        self.welcome_page.frame.pack(fill=tk.BOTH, expand=True)

    def browse_csv(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("Fichiers CSV", ".csv"), ("Tous les fichiers", ".*")]
        )
        if file_path:
            self.csv_path_var.set(file_path)

    def run_analysis(self):
        # Vérification du terme de recherche
        if not self.search_term_var.get().strip():
            messagebox.showwarning("Attention", "Veuillez saisir un terme à rechercher.")
            return

        self.run_btn.config(state=tk.DISABLED)
        self.status_var.set("Préparation de l'analyse...")
        self.progress_var.set(5)
        self.root.update_idletasks()

        analysis_thread = threading.Thread(target=self.perform_analysis, daemon=True)
        analysis_thread.start()

    def perform_analysis(self):
        try:
            self.root.after(100, self.update_progress, 10, "Chargement des données...")

            csv_path = self.csv_path_var.get()
            if not os.path.exists(csv_path):
                # Si le fichier n'existe pas, simuler l'analyse avec des données de démonstration
                self.root.after(100, self.update_progress, 20,
                                "Fichier non trouvé. Génération de données de démonstration...")
                self.generate_demo_results()

                self.root.after(100, self.update_progress, 90, "Génération des visualisations...")

                self.root.after(100, lambda: self.show_details(self.analysis_results))
                self.root.after(100, lambda: self.show_stats(self.analysis_results))

                self.root.after(100, self.update_progress, 100, "Analyse terminée (mode démo)")
                self.root.after(100, lambda: messagebox.showinfo("Information",
                                                                 "Fichier CSV non trouvé. Utilisation de données de démonstration."))
                return

            df = pd.read_csv(csv_path, encoding='latin-1', header=None)

            self.root.after(100, self.update_progress, 30, "Analyse en cours...")

            search_term = self.search_term_var.get()
            sample_size = int(self.sample_size_var.get())
            self.analysis_results = self.analyze_tweets(df, search_term, sample_size)

            self.root.after(100, self.update_progress, 70, "Sauvegarde des résultats...")

            self.save_results(self.analysis_results)

            self.root.after(100, self.update_progress, 90, "Génération des visualisations...")

            self.root.after(100, lambda: self.show_details(self.analysis_results))
            self.root.after(100, lambda: self.show_stats(self.analysis_results))

            self.root.after(100, self.update_progress, 100, "Analyse terminée avec succès")

            self.root.after(100, lambda: messagebox.showinfo("Succès", "Analyse des sentiments terminée avec succès!"))

        except Exception as e:
            print(f"Erreur dans perform_analysis: {str(e)}")
            # En cas d'erreur, utiliser des données démo pour montrer l'interface
            self.root.after(100, self.update_progress, 0, f"Erreur: {str(e)}")
            self.root.after(100, lambda: messagebox.showwarning("Erreur",
                                                                f"Échec de l'analyse: {str(e)}\nUtilisation de données de démonstration."))
            self.generate_demo_results()
            self.root.after(100, lambda: self.show_details(self.analysis_results))
            self.root.after(100, lambda: self.show_stats(self.analysis_results))
        finally:
            self.root.after(100, lambda: self.run_btn.config(state=tk.NORMAL))
            self.root.after(3000, lambda: self.progress_var.set(0))

    def update_progress(self, value, message):
        self.progress_var.set(value)
        self.status_var.set(message)
        self.root.update_idletasks()

    def generate_demo_results(self):
        """Génère des résultats de démonstration quand le fichier CSV n'est pas disponible"""
        sentiments = ['positif', 'neutre', 'negatif']
        demo_tweets = [
            "J'adore ce produit, il est génial!",
            "Le service client est correct, mais pourrait être amélioré",
            "Je déteste cette entreprise, jamais plus!",
            "Expérience moyenne, rien de spécial",
            "Incroyable! Je recommande vivement",
            "Très déçu par la qualité du produit",
            "Correct pour le prix payé",
            "Meilleur achat de l'année!",
            "Ne correspond pas à la description",
            "Livraison rapide et produit de qualité",
            "Totalement insatisfait, à éviter!",
            "Bon rapport qualité-prix, content de mon achat",
            "Super service, j'y retournerai",
            "Très long délai de livraison, c'est dommage",
            "La qualité s'est détériorée ces derniers temps",
            "Personnel accueillant et professionnel",
            "Impossible de contacter le service client",
            "Des améliorations ont été apportées, c'est mieux",
            "Problème résolu rapidement, merci",
            "Je ne comprends pas les bonnes critiques"
        ]

        self.analysis_results = []
        analyzer = SentimentIntensityAnalyzer()

        # Ajouter plus de tweets si nécessaire pour atteindre la taille d'échantillon demandée
        sample_size = min(int(self.sample_size_var.get()), 100)  # Limiter à 100 pour la démo
        while len(demo_tweets) < sample_size:
            demo_tweets.extend(demo_tweets[:min(len(demo_tweets), sample_size - len(demo_tweets))])

        for i in range(sample_size):
            tweet = demo_tweets[i % len(demo_tweets)]
            score = analyzer.polarity_scores(tweet)

            # Définir le sentiment en fonction du score compound au lieu de le choisir aléatoirement
            if score['compound'] >= 0.05:
                sentiment = 'positif'
            elif score['compound'] <= -0.05:
                sentiment = 'negatif'
            else:
                sentiment = 'neutre'

            self.analysis_results.append({
                'tweet': tweet,
                'tweet_short': tweet[:100] + ('...' if len(tweet) > 100 else ''),
                'score': score,
                'sentiment': sentiment
            })

    def analyze_tweets(self, df, search_term, sample_size):
        try:
            if hasattr(self, 'welcome_page') and hasattr(self.welcome_page, 'search_term_var'):
                original_term = self.welcome_page.search_term_var.get()
                print(f"Terme sélectionné depuis l'interface: '{original_term}'")
                search_term = original_term.lower()
            else:
                original_term = search_term
                search_term = search_term.lower()

            if not search_term or search_term.strip() == "":
                search_term = self.search_term_var.get().lower()
                original_term = self.search_term_var.get()

            analyzer = SentimentIntensityAnalyzer()

            df_processed = df.copy()
            if 5 in df_processed.columns:
                df_processed[5] = df_processed[5].astype(str)

            print(f"Recherche du terme: '{search_term}'")
            print(f"Nombre total de tweets: {len(df_processed)}")

            tweet_df = df_processed[[0, 5]].copy()
            tweet_df.columns = ['sentiment', 'tweet']

            filtered_df = tweet_df[tweet_df['tweet'].str.lower().str.contains(search_term, na=False)]

            print(f"Nombre de tweets trouvés contenant '{search_term}': {len(filtered_df)}")

            # Si aucun tweet n'est trouvé, retourner une liste vide
            if len(filtered_df) == 0:
                print(f"Aucun tweet contenant '{search_term}' n'a été trouvé.")
                self.root.after(0, self.update_progress, 40,
                                f"Aucun tweet trouvé pour le terme '{original_term}'")
                return []

            sample = filtered_df.sample(min(sample_size, len(filtered_df)))

            print(f"Analyse d'un échantillon de {len(sample)} tweets")

            results = []
            total = len(sample)

            for i, (_, row) in enumerate(sample.iterrows()):
                if i % 10 == 0:
                    progress = 30 + (i / total * 40)
                    self.root.after(0, self.update_progress, progress, f"Analyse en cours: {i + 1}/{total} tweets")

                score = analyzer.polarity_scores(row['tweet'])

                results.append({
                    'tweet': row['tweet'],
                    'tweet_short': row['tweet'][:150] + ('...' if len(row['tweet']) > 150 else ''),
                    'score': score,
                    'sentiment': self.get_sentiment_label(score['compound'])
                })

            return results

        except Exception as e:
            print(f"Erreur dans analyze_tweets: {str(e)}")
            self.root.after(0, self.update_progress, 50,
                            "Erreur lors de la recherche.")
            return []

    def save_results(self, results):
        self.data_path.mkdir(parents=True, exist_ok=True)
        with open(self.data_path / 'results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def export_results(self):
        if not self.analysis_results:
            messagebox.showwarning("Attention", "Aucun résultat à exporter. Lancez d'abord une analyse.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Exporter les résultats",
            defaultextension=".csv",
            filetypes=[("Fichier CSV", ".csv"), ("Fichier Excel", ".xlsx"), ("Fichier JSON", "*.json")]
        )

        if not file_path:
            return

        try:
            results_df = pd.DataFrame([
                {
                    'tweet': r['tweet'],
                    'sentiment': r['sentiment'],
                    'compound': r['score']['compound'],
                    'positive': r['score']['pos'],
                    'neutral': r['score']['neu'],
                    'negative': r['score']['neg']
                } for r in self.analysis_results
            ])

            if file_path.endswith('.csv'):
                results_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_path.endswith('.xlsx'):
                results_df.to_excel(file_path, index=False)
            elif file_path.endswith('.json'):
                results_df.to_json(file_path, orient='records', force_ascii=False, indent=2)

            messagebox.showinfo("Succès", f"Résultats exportés avec succès vers {file_path}")

        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'exportation:\n{str(e)}")

    def show_details(self, results):
        self.text_details.config(state=tk.NORMAL)
        self.text_details.delete(1.0, tk.END)

        theme = self.themes["blue"]
        self.text_details.config(bg=theme["text_bg"], fg=theme["fg"])

        if not results or len(results) == 0:
            self.text_details.insert(tk.END,
                                     f"Aucun tweet trouvé pour le terme recherché: '{self.search_term_var.get()}'.")
            self.text_details.config(state=tk.DISABLED)
            return

        positive = sum(1 for r in results if r['sentiment'] == 'positif')
        negative = sum(1 for r in results if r['sentiment'] == 'negatif')
        neutral = sum(1 for r in results if r['sentiment'] == 'neutre')
        total = len(results)

        # En-tête amélioré avec style
        self.text_details.insert(tk.END, "📊 ANALYSE DE SENTIMENT - RÉSUMÉ\n\n", "header")
        self.text_details.insert(tk.END, f"Terme recherché: ", "bold")
        self.text_details.insert(tk.END, f"{self.search_term_var.get()}\n")
        self.text_details.insert(tk.END, f"Nombre total de tweets analysés: ", "bold")
        self.text_details.insert(tk.END, f"{total}\n\n")

        # Résumé avec barres visuelles
        self.text_details.insert(tk.END, f"Tweets positifs: {positive} ({positive / total * 100:.1f}%) ", "positive")
        self.text_details.insert(tk.END, "🟢" * int((positive / total) * 30) + "\n", "positive")

        self.text_details.insert(tk.END, f"Tweets neutres: {neutral} ({neutral / total * 100:.1f}%) ", "neutral")
        self.text_details.insert(tk.END, "🟡" * int((neutral / total) * 30) + "\n", "neutral")

        self.text_details.insert(tk.END, f"Tweets négatifs: {negative} ({negative / total * 100:.1f}%) ", "negative")
        self.text_details.insert(tk.END, "🔴" * int((negative / total) * 30) + "\n\n", "negative")

        self.text_details.insert(tk.END, "📝 DÉTAILS DES TWEETS ANALYSÉS\n\n", "header")

        for i, r in enumerate(results, 1):
            sentiment_color = {
                'positif': "positive",
                'neutre': "neutral",
                'negatif': "negative"
            }.get(r['sentiment'], "normal")

            # Affichage amélioré avec séparation visuelle
            self.text_details.insert(tk.END, f"Tweet #{i} ", "bold")

            # Badge de sentiment
            badge = {"positif": "🟢", "neutre": "🟡", "negatif": "🔴"}.get(r['sentiment'], "⚪")
            self.text_details.insert(tk.END, f"{badge} {r['sentiment'].upper()} ", sentiment_color)

            # Score avec meilleure présentation
            self.text_details.insert(tk.END, f"(score: {r['score']['compound']:.3f})\n", "score")

            # Contenu du tweet
            self.text_details.insert(tk.END, f"{r['tweet']}\n")

            # Ligne de séparation
            self.text_details.insert(tk.END, "─" * 80 + "\n\n")

        # Configuration des styles de tags
        self.text_details.tag_configure("header", font=("Segoe UI", 14, "bold"),
                                        foreground=theme["highlight"])
        self.text_details.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        self.text_details.tag_configure("positive", foreground="#4CAF50")  # Vert plus vif
        self.text_details.tag_configure("neutral", foreground="#FFC107")  # Jaune plus vif
        self.text_details.tag_configure("negative", foreground="#F44336")  # Rouge plus vif
        self.text_details.tag_configure("score", foreground=theme["accent"], font=("Segoe UI", 10))

        self.text_details.config(state=tk.DISABLED)

    def open_web_interface(self):
        try:
            if not (self.frontend_path / "index.php").exists():
                raise FileNotFoundError("index.php introuvable")

            url = f"http://localhost/sentiment-analysis-web/frontend/index.php?t={int(time.time())}"
            webbrowser.open_new(url)

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'interface:\n{str(e)}")

    def open_results_folder(self):
        try:
            self.data_path.mkdir(parents=True, exist_ok=True)
            os.startfile(self.data_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{str(e)}")

    def show_stats(self, results):
        # Nettoyer l'onglet des statistiques
        for widget in self.stats_tab.winfo_children():
            widget.destroy()

        # Créer un canvas avec barre de défilement
        canvas = tk.Canvas(self.stats_tab, bg=self.themes["blue"]["bg"])
        scrollbar = ttk.Scrollbar(self.stats_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Blue.TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        theme = self.themes["blue"]

        # Titre principal
        header_frame = ttk.Frame(scrollable_frame, style="Blue.TFrame")
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        ttk.Label(header_frame, text="Statistiques d'Analyse de Sentiment",
                  style="Header.TLabel").pack(anchor=tk.CENTER)

        # Ligne de séparation
        separator = ttk.Separator(scrollable_frame, orient='horizontal')
        separator.pack(fill=tk.X, padx=20, pady=10)

        if not results or len(results) == 0:
            # Message d'absence de résultats plus attractif
            no_results_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
            no_results_frame.pack(fill=tk.X, padx=20, pady=20)

            ttk.Label(no_results_frame, text="🔍",
                      font=("Segoe UI", 36)).pack(pady=(20, 10))

            ttk.Label(no_results_frame,
                      text=f"Aucun tweet trouvé pour le terme recherché: '{self.search_term_var.get()}'.",
                      style="Subheader.TLabel").pack(pady=(0, 20))
            return

        # Calculer les statistiques
        positive = sum(1 for r in results if r['sentiment'] == 'positif')
        negative = sum(1 for r in results if r['sentiment'] == 'negatif')
        neutral = sum(1 for r in results if r['sentiment'] == 'neutre')
        total = len(results)

        compound_scores = [r['score']['compound'] for r in results]
        avg_compound = sum(compound_scores) / total if total > 0 else 0
        max_compound = max(compound_scores) if compound_scores else 0
        min_compound = min(compound_scores) if compound_scores else 0

        # Disposition en grille pour les statistiques principales
        stats_grid = ttk.Frame(scrollable_frame, style="Blue.TFrame")
        stats_grid.pack(fill=tk.X, padx=20, pady=10)

        # Première ligne
        self.create_stat_card(stats_grid, "Total Tweets", total, "#0F5B94", 0, 0)
        self.create_stat_card(stats_grid, "Score Moyen", f"{avg_compound:.3f}", theme["accent"], 0, 1)

        # Deuxième ligne
        self.create_stat_card(stats_grid, "Tweets Positifs",
                              f"{positive} ({positive / total * 100:.1f}%)" if total > 0 else "0 (0.0%)",
                              "#4CAF50", 1, 0)
        self.create_stat_card(stats_grid, "Score Max", f"{max_compound:.3f}", "#4CAF50", 1, 1)

        # Troisième ligne
        self.create_stat_card(stats_grid, "Tweets Neutres",
                              f"{neutral} ({neutral / total * 100:.1f}%)" if total > 0 else "0 (0.0%)",
                              "#FFC107", 2, 0)

        # Quatrième ligne
        self.create_stat_card(stats_grid, "Tweets Négatifs",
                              f"{negative} ({negative / total * 100:.1f}%)" if total > 0 else "0 (0.0%)",
                              "#F44336", 3, 0)
        self.create_stat_card(stats_grid, "Score Min", f"{min_compound:.3f}", "#F44336", 3, 1)

        # Graphique visuel de distribution des sentiments
        distribution_frame = ttk.LabelFrame(scrollable_frame, text="Distribution des Sentiments",
                                            style="Card.TFrame")
        distribution_frame.pack(fill=tk.X, padx=20, pady=10)

        # Calcul des pourcentages
        pos_percent = positive / total * 100 if total > 0 else 0
        neu_percent = neutral / total * 100 if total > 0 else 0
        neg_percent = negative / total * 100 if total > 0 else 0

        # Barre horizontale de distribution
        bar_canvas = tk.Canvas(distribution_frame, height=40, bg=theme["card_bg"],
                               highlightthickness=0)
        bar_canvas.pack(fill=tk.X, padx=20, pady=10)

        # Dessiner les segments de la barre
        bar_width = bar_canvas.winfo_reqwidth() - 40  # Marge de 20px de chaque côté

        # Couleurs plus vives
        pos_color = "#4CAF50"  # Vert
        neu_color = "#FFC107"  # Jaune
        neg_color = "#F44336"  # Rouge

        # Position initiale
        x_pos = 20

        # Segment positif
        pos_width = int(bar_width * (pos_percent / 100))
        bar_canvas.create_rectangle(x_pos, 10, x_pos + pos_width, 30, fill=pos_color, outline="")
        bar_canvas.create_text(x_pos + pos_width / 2, 40, text=f"{pos_percent:.1f}%",
                               fill=pos_color, font=("Segoe UI", 9, "bold"))
        x_pos += pos_width

        # Segment neutre
        neu_width = int(bar_width * (neu_percent / 100))
        bar_canvas.create_rectangle(x_pos, 10, x_pos + neu_width, 30, fill=neu_color, outline="")
        bar_canvas.create_text(x_pos + neu_width / 2, 40, text=f"{neu_percent:.1f}%",
                               fill=neu_color, font=("Segoe UI", 9, "bold"))
        x_pos += neu_width

        # Segment négatif
        neg_width = int(bar_width * (neg_percent / 100))
        bar_canvas.create_rectangle(x_pos, 10, x_pos + neg_width, 30, fill=neg_color, outline="")
        bar_canvas.create_text(x_pos + neg_width / 2, 40, text=f"{neg_percent:.1f}%",
                               fill=neg_color, font=("Segoe UI", 9, "bold"))

        # Légende
        legend_frame = ttk.Frame(distribution_frame, style="Card.TFrame")
        legend_frame.pack(fill=tk.X, padx=20, pady=10)

        # Créer des étiquettes colorées pour la légende
        ttk.Label(legend_frame, text="🟢 Positif",
                  font=("Segoe UI", 10, "bold"),
                  foreground=pos_color).pack(side=tk.LEFT, padx=20)

        ttk.Label(legend_frame, text="🟡 Neutre",
                  font=("Segoe UI", 10, "bold"),
                  foreground=neu_color).pack(side=tk.LEFT, padx=20)

        ttk.Label(legend_frame, text="🔴 Négatif",
                  font=("Segoe UI", 10, "bold"),
                  foreground=neg_color).pack(side=tk.LEFT, padx=20)

        # Affichez les tweets les plus positifs et négatifs s'il y en a
        if len(results) > 0:
            self.create_tweet_list(scrollable_frame, "Tweets les Plus Positifs",
                                   sorted(results, key=lambda x: x['score']['compound'], reverse=True)[:5],
                                   "#4CAF50")
            self.create_tweet_list(scrollable_frame, "Tweets les Plus Négatifs",
                                   sorted(results, key=lambda x: x['score']['compound'])[:5],
                                   "#F44336")

    def create_stat_card(self, parent, title, value, color, row, column):
        """Crée une carte de statistique moderne"""
        card = ttk.Frame(parent, style="Card.TFrame")
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

        # Un peu d'espace pour rendre la carte plus attrayante
        ttk.Label(card, text="", style="Card.TLabel").pack(pady=2)

        # Valeur en grand et en couleur
        ttk.Label(card, text=str(value), style="Card.TLabel",
                  font=("Segoe UI", 16, "bold"), foreground=color).pack(anchor=tk.CENTER, pady=5)

        # Titre en dessous
        ttk.Label(card, text=title, style="Card.TLabel",
                  font=("Segoe UI", 10)).pack(anchor=tk.CENTER, pady=(0, 5))

        # Configurer l'expansion de la grille
        parent.grid_columnconfigure(column, weight=1)

    def create_tweet_list(self, parent, title, tweets, color):
        """Affiche une liste de tweets avec un style modernisé"""
        frame = ttk.LabelFrame(parent, text=title, style="Card.TFrame")
        frame.pack(fill=tk.X, padx=20, pady=10)

        # Titre avec couleur
        header = ttk.Label(frame, text=title, style="Card.TLabel",
                           font=("Segoe UI", 12, "bold"), foreground=color)
        header.pack(anchor=tk.W, pady=(5, 15))

        # Style moderne pour les tweets
        for i, tweet in enumerate(tweets, 1):
            tweet_frame = ttk.Frame(frame, style="Card.TFrame")
            tweet_frame.pack(fill=tk.X, padx=5, pady=5)

            # En-tête du tweet
            header_frame = ttk.Frame(tweet_frame, style="Card.TFrame")
            header_frame.pack(fill=tk.X, padx=5, pady=2)

            # Numéro et score
            ttk.Label(header_frame,
                      text=f"#{i} • Score: {tweet['score']['compound']:.3f}",
                      style="Card.TLabel",
                      font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

            # Badge de sentiment
            badge = {"positif": "🟢", "neutre": "🟡", "negatif": "🔴"}.get(tweet['sentiment'], "⚪")
            ttk.Label(header_frame, text=f"{badge} {tweet['sentiment'].upper()}",
                      style="Card.TLabel", foreground=color).pack(side=tk.RIGHT)

            # Contenu du tweet dans un cadre
            text_frame = ttk.Frame(tweet_frame, style="Card.TFrame", padding=5)
            text_frame.pack(fill=tk.X, padx=5, pady=2)

            text = tk.Text(text_frame, wrap=tk.WORD, height=3,
                           bg="white", fg=self.themes["blue"]["fg"],
                           font=("Segoe UI", 9), padx=10, pady=10,
                           relief="flat", borderwidth=0)
            text.insert(tk.END, tweet['tweet'])
            text.config(state=tk.DISABLED)
            text.pack(fill=tk.X)

            # Ligne de séparation
            if i < len(tweets):
                ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)

    @staticmethod
    def get_sentiment_label(score):
        if score >= 0.05: return "positif"
        if score <= -0.05: return "negatif"
        return "neutre"
    def show_welcome_page(self):
        """Affiche la page d'accueil pour permettre de changer le sujet d'analyse"""
        if self.main_frame:
            self.main_frame.pack_forget()
        self.welcome_page.frame.pack(fill=tk.BOTH, expand=True)
        # Réinitialiser l'interface de bienvenue pour permettre un nouveau choix
        self.welcome_page.setup_ui()


import math  # Ajouter cet import

import math  # Ajouter cet import

import math  # Ajouter cet import


class WelcomePage:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.frame = ttk.Frame(root)

        # Configuration de la fenêtre avec barre de titre standard
        root.title("SAZAfeels - Analyse de Sentiment")

        # Style configuration - bleu ciel amélioré
        self.bg_color = "#E8F4FD"  # Fond bleu ciel plus vif
        self.fg_color = "#1A3A5C"  # Texte bleu plus foncé
        self.accent_color = "#4CA3D4"  # Bleu medium
        self.button_color = "#2196F3"  # Bleu vif plus moderne
        self.highlight_color = "#1E88E5"  # Bleu vif
        self.form_bg_color = "#F5FAFF"  # Bleu ciel plus clair pour le formulaire
        self.light_blue_text = "#87CEEB"  # Bleu ciel clair pour le texte de bienvenue

        # Variable for the selected search term
        self.search_term_var = tk.StringVar()
        self.search_term_var.set("")

        # Variables pour les animations
        self.animation_running = True
        self.particles = []
        self.floating_elements = []

        # Logo qui servira d'image de fond pour la page d'accueil
        self.logo_background = None
        try:
            # Charger le logo comme image d'arrière-plan pour la page d'accueil
            logo_img = Image.open("logo.jpg")  # Utiliser le logo comme fond
            # Redimensionner pour qu'il couvre bien l'écran
            logo_img = logo_img.resize((1200, 800), Image.LANCZOS)
            self.logo_background = ImageTk.PhotoImage(logo_img)
        except Exception as e:
            print(f"Erreur lors du chargement du logo comme arrière-plan: {e}")

        # Image de fond pour la page principale
        self.background_image = None
        try:
            # Charger l'image d'arrière-plan pour la page principale
            bg_img = Image.open("twitter.jpg")
            # Redimensionner pour s'assurer qu'elle couvre tout l'écran
            bg_img = bg_img.resize((1200, 800), Image.LANCZOS)
            self.background_image = ImageTk.PhotoImage(bg_img)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image d'arrière-plan: {e}")

        # Configure the welcome page
        self.setup_ui()

    def setup_ui(self):
        """Set up the welcome page interface."""
        # Vider tous les widgets sauf le frame principal
        for widget in self.root.winfo_children():
            if widget != self.frame:
                widget.destroy()

        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.configure(style="Blue.TFrame")

        # Première page simple avec le logo en plein écran et animation de bienvenue
        splash_frame = ttk.Frame(self.frame, style="Blue.TFrame")
        splash_frame.pack(fill=tk.BOTH, expand=True)

        # Utiliser un Canvas pour afficher l'image en plein écran
        if self.logo_background:
            self.bg_canvas = tk.Canvas(splash_frame, width=1200, height=800, highlightthickness=0)
            self.bg_canvas.pack(fill=tk.BOTH, expand=True)
            self.bg_canvas.create_image(0, 0, image=self.logo_background, anchor=tk.NW)

            # Créer des particules flottantes
            self.create_floating_particles()

            # Texte de bienvenue avec couleur bleu ciel clair
            self.welcome_text = self.bg_canvas.create_text(600, 400, text="",
                                                           font=("Segoe UI", 36, "bold"),
                                                           fill=self.light_blue_text,  # Bleu ciel clair
                                                           anchor=tk.CENTER)

            # Texte secondaire aussi en bleu ciel
            self.subtitle = self.bg_canvas.create_text(600, 480, text="",
                                                       font=("Segoe UI", 24),
                                                       fill=self.light_blue_text,  # Bleu ciel clair
                                                       anchor=tk.CENTER, state='hidden')

            # Démarrer les animations
            self.animate_welcome_text()

        else:
            # Fallback si l'image ne charge pas
            ttk.Label(splash_frame, text="🧠", font=("Segoe UI", 48)).pack(pady=10)
            ttk.Label(splash_frame, text="Bienvenue sur SAZAfeels",
                      font=("Segoe UI", 36, "bold"), foreground=self.light_blue_text).pack(pady=5)
            ttk.Label(splash_frame, text="Analyse de sentiments Twitter",
                      font=("Segoe UI", 24), foreground=self.light_blue_text).pack(pady=5)

        # Bouton pour passer à la page principale après 3 secondes
        self.root.after(3000, self.show_main_page)

    def create_floating_particles(self):
        """Crée des particules flottantes pour un effet magique"""
        for _ in range(30):
            x = random.randint(0, 1200)
            y = random.randint(0, 800)
            size = random.randint(2, 5)
            speed = random.uniform(0.5, 2)
            color = random.choice([self.accent_color, self.light_blue_text, "#FFFFFF"])

            particle = self.bg_canvas.create_oval(x - size, y - size, x + size, y + size,
                                                  fill=color, outline="")

            self.particles.append({
                'id': particle,
                'x': x,
                'y': y,
                'speed': speed,
                'direction': random.uniform(0, 2 * 3.14159)
            })

        self.animate_particles()

    def animate_particles(self):
        """Anime les particules"""
        if not self.animation_running:
            return

        for particle in self.particles:
            # Déplacement
            particle['x'] += math.cos(particle['direction']) * particle['speed']
            particle['y'] += math.sin(particle['direction']) * particle['speed']

            # Rebond sur les bords
            if particle['x'] < 0 or particle['x'] > 1200:
                particle['direction'] = 3.14159 - particle['direction']
            if particle['y'] < 0 or particle['y'] > 800:
                particle['direction'] = -particle['direction']

            # Mise à jour de la position
            self.bg_canvas.coords(particle['id'],
                                  particle['x'] - 2, particle['y'] - 2,
                                  particle['x'] + 2, particle['y'] + 2)

        self.root.after(30, self.animate_particles)

    def animate_welcome_text(self):
        """Animation de frappe pour le texte de bienvenue"""
        full_text = "Bienvenue sur SAZAfeels"

        def type_char(index=0):
            if index <= len(full_text):
                self.bg_canvas.itemconfig(self.welcome_text, text=full_text[:index])
                self.root.after(100, lambda: type_char(index + 1))
            else:
                # Après l'animation de frappe, faire apparaître le sous-titre
                self.animate_subtitle_fade_in()

        type_char()

    def animate_subtitle_fade_in(self):
        """Fait apparaître le sous-titre avec un effet de fondu"""
        self.bg_canvas.itemconfig(self.subtitle, text="Analyse de sentiments Twitter", state='normal')

        # Animation de zoom
        for i in range(10):
            scale_factor = 0.5 + (i / 10) * 0.5
            font_size = int(24 * scale_factor)
            self.bg_canvas.itemconfig(self.subtitle, font=("Segoe UI", font_size))
            self.bg_canvas.update()
            time.sleep(0.05)

    def show_main_page(self):
        """Affiche la page principale avec le fond twitter et animations"""
        self.animation_running = False  # Arrêter les animations précédentes

        # Effacer la page de démarrage
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Canvas pour l'image de fond plein écran
        self.main_canvas = tk.Canvas(self.frame, width=1200, height=800, highlightthickness=0)
        self.main_canvas.pack(fill=tk.BOTH, expand=True)

        # Afficher l'image de fond si disponible
        if self.background_image:
            self.main_canvas.create_image(0, 0, image=self.background_image, anchor=tk.NW)

            # Superposer un overlay semi-transparent pour améliorer la lisibilité
            self.main_canvas.create_rectangle(0, 0, 1200, 800, fill="#000000", stipple="gray50", outline="")

        # Créer des petits points blancs comme dans la première page
        self.create_white_dots()

        # Créer un formulaire amélioré
        form_width, form_height = 600, 400
        center_x, center_y = 600, 400

        # Rectangle moderne pour le formulaire
        self.form_bg = self.create_modern_form(center_x, center_y, form_width, form_height)

        # Animation d'apparition du formulaire
        self.animate_form_appearance(center_x, center_y)

        # Ajouter des indicateurs animés
        self.create_animated_indicators()

    def create_white_dots(self):
        """Crée des petits points blancs animés comme dans la première page"""
        self.white_dots = []

        for _ in range(40):
            x = random.randint(0, 1200)
            y = random.randint(0, 800)
            size = random.randint(1, 3)
            speed = random.uniform(0.3, 1.5)

            dot = self.main_canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill="#FFFFFF",
                outline=""
            )

            self.white_dots.append({
                'id': dot,
                'x': x,
                'y': y,
                'speed': speed,
                'direction': random.uniform(0, 2 * 3.14159)
            })

        self.animate_white_dots()

    def animate_white_dots(self):
        """Anime les petits points blancs"""
        for dot in self.white_dots:
            # Déplacement
            dot['x'] += math.cos(dot['direction']) * dot['speed']
            dot['y'] += math.sin(dot['direction']) * dot['speed']

            # Rebond sur les bords
            if dot['x'] < 0 or dot['x'] > 1200:
                dot['direction'] = 3.14159 - dot['direction']
            if dot['y'] < 0 or dot['y'] > 800:
                dot['direction'] = -dot['direction']

            # Mise à jour de la position
            self.main_canvas.coords(dot['id'],
                                    dot['x'] - 1, dot['y'] - 1,
                                    dot['x'] + 1, dot['y'] + 1)

        self.root.after(40, self.animate_white_dots)

    def create_modern_form(self, center_x, center_y, width, height):
        """Crée un formulaire moderne avec coins arrondis"""
        # Rectangle avec coins arrondis et effet moderne
        radius = 30

        # Créer les points pour un rectangle avec coins arrondis
        x1, y1 = center_x - width / 2, center_y - height / 2
        x2, y2 = center_x + width / 2, center_y + height / 2

        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]

        # Créer le fond avec effet de verre dépoli
        form_bg = self.main_canvas.create_polygon(points, fill="#FFFFFF",
                                                  stipple="gray25",
                                                  outline=self.button_color,
                                                  width=2,
                                                  smooth=True)

        # Ajouter un effet d'ombre
        shadow = self.main_canvas.create_polygon(
            [p + 5 if i % 2 == 0 else p + 5 for i, p in enumerate(points)],
            fill="#000000", stipple="gray75", smooth=True)
        self.main_canvas.tag_lower(shadow)

        return form_bg

    def animate_form_appearance(self, center_x, center_y):
        """Animation d'apparition du formulaire avec effets"""
        # Titre avec animation de frappe
        self.title_text = self.main_canvas.create_text(
            center_x,
            center_y - 150,
            text="",
            font=("Segoe UI", 32, "bold"),
            fill="#FFFFFF",
            anchor=tk.CENTER
        )

        # Animation de frappe pour le titre
        self.type_title_text()

        # Sous-titre avec effet de fade in
        self.label_text = self.main_canvas.create_text(
            center_x,
            center_y - 80,
            text="Entrez le sujet à analyser:",
            font=("Segoe UI", 20),
            fill="#FFFFFF",
            anchor=tk.CENTER,
            state='hidden'
        )

        # Faire apparaître le sous-titre après un délai
        self.root.after(1500, lambda: self.fade_in_text(self.label_text))

        # Entry avec animation de fade in
        entry_frame = tk.Frame(self.main_canvas, bg="#FFFFFF", bd=2, relief="solid")
        entry_frame.config(highlightbackground=self.button_color, highlightthickness=2)

        self.entry = tk.Entry(
            entry_frame,
            textvariable=self.search_term_var,
            width=35,
            font=("Segoe UI", 16),
            bg="#FFFFFF",
            fg=self.fg_color,
            relief=tk.FLAT,
            bd=5
        )
        self.entry.pack(padx=15, pady=10)

        # Créer l'entry window mais le garder caché
        self.entry_window = self.main_canvas.create_window(
            center_x,
            center_y,
            window=entry_frame,
            anchor=tk.CENTER,
            state='hidden'
        )

        # Animation de fade in pour l'entry
        self.root.after(2000, lambda: self.fade_in_entry())

        # Bouton avec animation
        self.root.after(2500, lambda: self.create_rounded_button(center_x, center_y + 80))

    def type_title_text(self):
        """Animation de frappe pour le titre"""
        title_text = "Analyse de Sentiment Twitter"

        def type_char(index=0):
            if index <= len(title_text):
                self.main_canvas.itemconfig(self.title_text, text=title_text[:index])
                self.root.after(50, lambda: type_char(index + 1))

        type_char()

    def fade_in_text(self, text_id):
        """Animation de fade in pour un texte"""
        self.main_canvas.itemconfig(text_id, state='normal')

        # Effet de fade in avec changement d'opacité simulé
        for i in range(10):
            opacity = i / 10
            alpha = int(255 * opacity)
            color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            self.main_canvas.itemconfig(text_id, fill=color)
            self.root.update()
            time.sleep(0.05)

        self.main_canvas.itemconfig(text_id, fill="#FFFFFF")

    def fade_in_entry(self):
        """Animation de fade in pour l'entry"""
        self.main_canvas.itemconfig(self.entry_window, state='normal')
        self.entry.focus_set()

    def create_rounded_button(self, x, y):
        """Crée un bouton simple avec coins légèrement arrondis"""
        button_frame = tk.Frame(self.main_canvas, bg=self.button_color, highlightthickness=0)

        # Créer le bouton avec le style ttk pour avoir des coins légèrement arrondis
        style = ttk.Style()
        style.configure("Rounded.TButton",
                        background=self.button_color,
                        foreground="white",
                        font=("Segoe UI", 16, "bold"),
                        borderwidth=0,
                        relief="flat")

        # Créer un simple bouton
        self.button = ttk.Button(
            button_frame,
            text="Lancer l'analyse",
            style="Rounded.TButton",
            command=self.start_app,
            width=20
        )
        self.button.pack(padx=20, pady=10)

        # Créer le window pour le bouton
        self.button_window = self.main_canvas.create_window(
            x,
            y + 100,
            window=button_frame,
            anchor=tk.CENTER,
            state='hidden'
        )

        # Bindings pour les effets de survol
        self.button.bind("<Enter>", lambda e: self.on_button_enter(e))
        self.button.bind("<Leave>", lambda e: self.on_button_leave(e))

        # Animation de fade in pour le bouton
        self.fade_in_button()

    def on_button_enter(self, event):
        """Effet au survol du bouton"""
        event.widget.configure(cursor="hand2")
        # Changer légèrement la couleur au survol
        darker_color = self.darken_color(self.button_color, 0.8)
        event.widget.configure(style="Hover.TButton")
        style = ttk.Style()
        style.configure("Hover.TButton",
                        background=darker_color,
                        foreground="white",
                        font=("Segoe UI", 16, "bold"),
                        borderwidth=0,
                        relief="flat")

    def on_button_leave(self, event):
        """Effet quand on quitte le bouton"""
        event.widget.configure(style="Rounded.TButton")

    def fade_in_button(self):
        """Animation de fade in pour le bouton"""
        self.main_canvas.itemconfig(self.button_window, state='normal')

        # Ajouter un petit effet de rebond
        def bounce(height=0, direction=1):
            if direction == 1 and height < 10:
                self.main_canvas.move(self.button_window, 0, -1)
                self.root.after(20, lambda: bounce(height + 1, 1))
            elif direction == -1 and height > 0:
                self.main_canvas.move(self.button_window, 0, 1)
                self.root.after(20, lambda: bounce(height - 1, -1))
            elif direction == 1:
                bounce(height, -1)

        self.root.after(100, bounce)

    def on_button_hover(self, canvas, button_shape):
        """Effet au survol du bouton"""
        canvas.itemconfig(button_shape, fill=self.darken_color(self.button_color))
        canvas.config(cursor="hand2")

    def on_button_leave(self, canvas, button_shape):
        """Effet quand on quitte le bouton"""
        canvas.itemconfig(button_shape, fill=self.button_color)

    def create_animated_indicators(self):
        """Crée des indicateurs animés"""
        trend_indicators = ["#️⃣", "💬", "📊", "📱", "🔍", "📈", "📉", "🌐", "💼", "🔄"]

        self.animated_indicators = []
        for i in range(20):
            indicator = random.choice(trend_indicators)
            x = random.randint(0, 1200)
            y = random.randint(0, 800)
            size = random.randint(10, 16)
            opacity = random.uniform(0.2, 0.7)

            # Créer un texte semi-transparent
            indicator_id = self.main_canvas.create_text(x, y, text=indicator,
                                                        font=("Segoe UI", size),
                                                        fill=f"#{int(255 * opacity):02x}FFFFFF")

            self.animated_indicators.append({
                'id': indicator_id,
                'x': x,
                'y': y,
                'speed': random.uniform(0.5, 1.5),
                'direction': random.uniform(0, 2 * 3.14159)
            })

        self.animate_indicators()

    def animate_indicators(self):
        """Anime les indicateurs de tendance"""
        for indicator in self.animated_indicators:
            # Déplacement lent
            indicator['x'] += math.cos(indicator['direction']) * indicator['speed']
            indicator['y'] += math.sin(indicator['direction']) * indicator['speed']

            # Rebond sur les bords
            if indicator['x'] < 0 or indicator['x'] > 1200:
                indicator['direction'] = 3.14159 - indicator['direction']
            if indicator['y'] < 0 or indicator['y'] > 800:
                indicator['direction'] = -indicator['direction']

            # Mise à jour de la position
            self.main_canvas.coords(indicator['id'], indicator['x'], indicator['y'])

        self.root.after(50, self.animate_indicators)

    def darken_color(self, hex_color, factor=0.8):
        """Assombrit une couleur hexadécimale"""
        # Convertir hex en RGB
        h = hex_color.lstrip('#')
        rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

        # Assombrir
        rgb_dark = tuple(int(c * factor) for c in rgb)

        # Reconvertir en hex
        return '#{:02x}{:02x}{:02x}'.format(rgb_dark[0], rgb_dark[1], rgb_dark[2])

    def start_app(self):
        """Validate the user's input and start the main application."""
        selected_topic = self.search_term_var.get().strip()

        if not selected_topic:
            # Animation d'erreur - faire trembler l'entrée
            self.shake_entry()
            messagebox.showwarning("Attention", "Veuillez saisir un sujet à analyser.")
            return

        print(f"Analyse démarrée pour : {selected_topic}")

        # Transférer la valeur recherchée à l'application principale
        self.app.search_term_var.set(selected_topic)

        # Arrêter toutes les animations
        self.animation_running = False

        # S'assurer que le frame est bien caché
        self.frame.pack_forget()

        # Appeler setup_ui de l'application principale
        self.app.setup_ui()

    def shake_entry(self):
        """Animation de tremblement pour l'erreur"""
        # Obtenir les coordonnées actuelles de l'entrée
        coords = self.main_canvas.coords(self.entry_window)
        original_x = coords[0]

        for _ in range(3):
            for offset in [10, -10, 8, -8, 5, -5, 2, -2, 0]:
                self.main_canvas.coords(self.entry_window, original_x + offset, coords[1])
                self.main_canvas.update()
                time.sleep(0.02)

if __name__ == "__main__":
    # Création de la fenêtre principale avec thème
    root = ThemedTk(theme="arc")
    root.tk_setPalette(
        background="#E8F4FD",  # Fond bleu ciel amélioré
        foreground="#1A3A5C",  # Texte bleu foncé
        activeBackground="#4CA3D4",  # Bleu medium pour les éléments actifs
        activeForeground="white",  # Texte blanc pour les éléments actifs
    )

    # Centrage de la fenêtre
    window_width = 1200
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

    # Tentative d'application d'un icône
    try:
        root.iconbitmap("logo.ico")
    except:
        pass

    # Lancement de l'application
    app = SentimentAnalysisApp(root)
    root.mainloop()