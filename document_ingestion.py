"""
Document Ingestion Service for RAG (Retrieval-Augmented Generation)
Processes PDFs, markdown, text files, and web URLs for VC best practices knowledge base
"""
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import hashlib

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False


class DocumentIngestionService:
    """Service for ingesting and processing documents for RAG"""
    
    def __init__(self, embedding_service=None):
        """
        Initialize document ingestion service
        
        Args:
            embedding_service: EmbeddingService instance for generating embeddings
        """
        self.embedding_service = embedding_service
        self.logger = logging.getLogger(__name__)
        self.documents: List[Dict] = []  # Store document chunks
    
    def ingest_file(
        self, 
        file_path: str, 
        doc_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Ingest a document file and return chunks
        
        Args:
            file_path: Path to the document file
            doc_type: Type of document ('pdf', 'md', 'txt', or None for auto-detect)
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of document chunks with text and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect file type if not specified
        if doc_type is None:
            doc_type = self._detect_file_type(file_path)
        
        # Read document content
        text_content = self._read_file(file_path, doc_type)
        
        if not text_content:
            self.logger.warning(f"Empty document: {file_path}")
            return []
        
        # Chunk the document
        chunks = self._chunk_text(text_content, file_path.name)
        
        # Add metadata
        doc_metadata = {
            'source': str(file_path),
            'filename': file_path.name,
            'doc_type': doc_type,
            'file_hash': self._hash_file(file_path),
            **(metadata or {})
        }
        
        for chunk in chunks:
            chunk['metadata'] = {**doc_metadata, **chunk.get('metadata', {})}
        
        self.logger.info(f"Ingested {file_path.name}: {len(chunks)} chunks")
        return chunks
    
    def ingest_text(
        self, 
        text: str, 
        source_name: str = "inline",
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Ingest text directly (for inline text input)
        
        Args:
            text: Text content to ingest
            source_name: Name for this text source
            metadata: Optional metadata
            
        Returns:
            List of document chunks
        """
        chunks = self._chunk_text(text, source_name)
        
        doc_metadata = {
            'source': source_name,
            'filename': source_name,
            'doc_type': 'text',
            **(metadata or {})
        }
        
        for chunk in chunks:
            chunk['metadata'] = {**doc_metadata, **chunk.get('metadata', {})}
        
        return chunks
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Auto-detect file type from extension"""
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.md', '.markdown']:
            return 'md'
        elif ext == '.txt':
            return 'txt'
        else:
            # Default to text
            self.logger.warning(f"Unknown file type: {ext}, treating as text")
            return 'txt'
    
    def _read_file(self, file_path: Path, doc_type: str) -> str:
        """Read file content based on type"""
        if doc_type == 'pdf':
            return self._read_pdf(file_path)
        elif doc_type == 'md':
            return self._read_markdown(file_path)
        elif doc_type == 'txt':
            return self._read_text(file_path)
        else:
            return self._read_text(file_path)  # Default
    
    def _read_pdf(self, file_path: Path) -> str:
        """Read PDF file"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not available. Install with: pip install PyPDF2")
        
        try:
            text_content = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
            
            return '\n\n'.join(text_content)
        except Exception as e:
            self.logger.error(f"Error reading PDF {file_path}: {e}")
            raise
    
    def _read_markdown(self, file_path: Path) -> str:
        """Read markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Optionally convert markdown to plain text
            if MARKDOWN_AVAILABLE:
                # Just return raw markdown (can convert to HTML/text if needed)
                return content
            else:
                return content
        except Exception as e:
            self.logger.error(f"Error reading markdown {file_path}: {e}")
            raise
    
    def _read_text(self, file_path: Path) -> str:
        """Read plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading text file {file_path}: {e}")
            raise
    
    def _chunk_text(
        self, 
        text: str, 
        source_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Dict]:
        """
        Split text into chunks for embedding
        
        Args:
            text: Text to chunk
            source_name: Name of source
            chunk_size: Target size of each chunk (characters)
            chunk_overlap: Overlap between chunks (characters)
            
        Returns:
            List of chunk dictionaries with 'text' and 'chunk_index'
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        
        # Simple chunking strategy: split by paragraphs, then by size
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph would exceed chunk size, finalize current chunk
            if current_chunk and len(current_chunk) + len(para) > chunk_size:
                chunks.append({
                    'text': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'metadata': {}
                })
                
                # Start new chunk with overlap (last part of previous chunk)
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + '\n\n' + para
                else:
                    current_chunk = para
                
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += '\n\n' + para
                else:
                    current_chunk = para
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_index': chunk_index,
                'metadata': {}
            })
        
        # If text is very short, ensure we have at least one chunk
        if not chunks and text.strip():
            chunks.append({
                'text': text.strip(),
                'chunk_index': 0,
                'metadata': {}
            })
        
        self.logger.debug(f"Chunked {source_name}: {len(text)} chars → {len(chunks)} chunks")
        return chunks
    
    def _hash_file(self, file_path: Path) -> str:
        """Generate hash of file content for change detection"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            self.logger.warning(f"Could not hash file {file_path}: {e}")
            return ""
    
    def ingest_url(
        self,
        url: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Ingest content from a web URL
        
        Args:
            url: Web URL to scrape
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of document chunks with text and metadata
        """
        if not WEB_SCRAPING_AVAILABLE:
            raise ImportError(
                "Web scraping not available. Install with: pip install requests beautifulsoup4"
            )
        
        # Validate URL
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        self.logger.info(f"Scraping content from URL: {url}")
        
        try:
            # Fetch web page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text content
            text_content = soup.get_text(separator='\n\n', strip=True)
            
            # Clean up text (remove excessive whitespace)
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\n'.join(chunk for chunk in chunks if chunk)
            
            if not text_content or len(text_content) < 100:
                self.logger.warning(f"Minimal content extracted from URL: {url}")
                return []
            
            # Extract title if available
            title = None
            if soup.title:
                title = soup.title.string.strip()
            
            # Chunk the text
            chunks = self._chunk_text(text_content, url)
            
            # Add metadata
            parsed_url = urlparse(url)
            doc_metadata = {
                'source': url,
                'filename': parsed_url.netloc + parsed_url.path,
                'doc_type': 'web',
                'url': url,
                'domain': parsed_url.netloc,
                'title': title,
                **(metadata or {})
            }
            
            for chunk in chunks:
                chunk['metadata'] = {**doc_metadata, **chunk.get('metadata', {})}
            
            self.logger.info(f"Ingested URL {url}: {len(chunks)} chunks")
            return chunks
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing URL {url}: {e}")
            raise
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def ingest_urls(self, urls: List[str], metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Ingest content from multiple URLs
        
        Args:
            urls: List of URLs to scrape
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of all document chunks from all URLs
        """
        all_chunks = []
        for url in urls:
            try:
                chunks = self.ingest_url(url, metadata)
                all_chunks.extend(chunks)
            except Exception as e:
                self.logger.warning(f"Skipping URL {url} due to error: {e}")
                continue
        return all_chunks
    
    def clear_documents(self):
        """Clear all ingested documents"""
        self.documents = []
        self.logger.info("Cleared all documents")
