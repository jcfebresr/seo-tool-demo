from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Modelo NLP (se carga bajo demanda)
_model = None

def get_model():
    """Carga el modelo NLP solo cuando se necesita"""
    global _model
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model

def detect_category_from_url(url):
    """Detecta categoría basada en patrones en la URL"""
    
    url_lower = url.lower().strip()
    
    try:
        parsed = urlparse(url_lower)
        path = parsed.path.strip('/')
        
        if not path:
            return "Homepage"
        
        segments = [s for s in path.split('/') if s]
        
        if not segments:
            return "Homepage"
        
        first_segment = segments[0]
        
        # Patrones comunes
        patterns = {
            'Producto': ['shop', 'producto', 'product', 'productos', 'products', 'item', 'p'],
            'Categoria Producto': ['categoria-producto', 'category', 'categoria', 'categories', 'cat'],
            'Marca': ['marca', 'brand', 'brands', 'marcas'],
            'Blog': ['blog', 'articulo', 'article', 'post', 'news', 'noticias'],
            'Contacto': ['contacto', 'contact', 'contact-us'],
            'Nosotros': ['nosotros', 'about', 'about-us', 'quienes-somos', 'empresa'],
            'Wishlist': ['wishlist', 'favoritos', 'favorites', 'lista-deseos'],
            'Carrito': ['cart', 'carrito', 'checkout', 'bag'],
            'Mi Cuenta': ['mi-cuenta', 'account', 'profile', 'perfil', 'dashboard']
        }
        
        # Buscar match
        for category, keywords in patterns.items():
            if any(keyword in first_segment for keyword in keywords):
                return category
        
        # Si tiene 2+ segmentos, probablemente es producto
        if len(segments) >= 2:
            return "Producto"
        
        return None
        
    except:
        return None

def categorize_urls_automatic(urls):
    """Categoriza URLs automáticamente por patrones"""
    
    categories_found = set()
    results = []
    
    for url in urls:
        detected = detect_category_from_url(url)
        
        if detected:
            categories_found.add(detected)
            results.append({
                'url': url,
                'category': detected,
                'confidence': 1.0
            })
        else:
            results.append({
                'url': url,
                'category': 'Otros',
                'confidence': 0.0
            })
    
    master_categories = sorted(list(categories_found))
    
    return results, master_categories

def categorize_urls_nlp(urls, master_categories):
    """Categoriza URLs usando NLP con similitud semántica"""
    
    model = get_model()
    
    # Generar embeddings de categorías maestras
    master_embeddings = model.encode(master_categories)
    
    results = []
    
    for url in urls:
        detected = detect_category_from_url(url)
        
        if not detected:
            results.append({
                'url': url,
                'category': 'Otros',
                'confidence': 0.0
            })
            continue
        
        # Match exacto
        if detected in master_categories:
            results.append({
                'url': url,
                'category': detected,
                'confidence': 1.0
            })
            continue
        
        # Similitud semántica
        detected_embedding = model.encode([detected])
        similarities = cosine_similarity(detected_embedding, master_embeddings)[0]
        
        max_idx = np.argmax(similarities)
        max_sim = similarities[max_idx]
        
        if max_sim >= 0.6:
            results.append({
                'url': url,
                'category': master_categories[max_idx],
                'confidence': float(max_sim)
            })
        else:
            results.append({
                'url': url,
                'category': detected,
                'confidence': 0.5
            })
    
    return results

def categorize_urls_manual(urls, manual_categories):
    """Categoriza URLs usando categorías definidas manualmente"""
    
    results = []
    
    for url in urls:
        detected = detect_category_from_url(url)
        
        if detected in manual_categories:
            results.append({
                'url': url,
                'category': detected,
                'confidence': 1.0
            })
        else:
            results.append({
                'url': url,
                'category': detected if detected else 'Otros',
                'confidence': 0.5 if detected else 0.0
            })
    
    return results