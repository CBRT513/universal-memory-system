#!/usr/bin/env python3
"""
Universal AI Memory System - Core Memory Service
Production-ready memory service with SQLite + vector embeddings
"""

# Workspace configuration - automatically detect personal vs work
import sys
from pathlib import Path
sys.path.insert(0, '/usr/local/share/universal-memory-system')
try:
    from workspace_config import config
    # This automatically sets up the right database and port
    import os
    os.environ['MEMORY_API_PORT'] = str(config.api_port)
    os.environ['MEMORY_DB_PATH'] = config.database_path
except ImportError:
    pass  # Fallback to defaults if workspace config not available

import os
import sys
import json
import sqlite3
import hashlib
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from contextlib import contextmanager

# Third-party imports with fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None
    print("Warning: numpy not available. Some vector operations disabled.")

try:
    import hnswlib
    HAS_HNSWLIB = HAS_NUMPY  # hnswlib needs numpy
except ImportError:
    HAS_HNSWLIB = False
    
if not HAS_HNSWLIB:
    print("Warning: Vector search disabled (requires numpy and hnswlib).")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingProvider:
    """Base class for embedding providers"""
    
    def __init__(self):
        self.dimension = 384  # Default dimension
        self.model_name = "unknown"
    
    def get_embedding(self, text: str) -> Optional[Any]:  # Returns np.ndarray when available
        """Get embedding vector for text"""
        raise NotImplementedError
    
    def get_embeddings(self, texts: List[str]) -> List[Optional[Any]]:  # Returns List[np.ndarray] when available
        """Get embeddings for multiple texts"""
        return [self.get_embedding(text) for text in texts]
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return False

class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence transformer provider"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        super().__init__()
        self.model_name = model_name
        self.model = None
        self.dimension = 384
        
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Loaded SentenceTransformer: {model_name} (dim: {self.dimension})")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer: {e}")
                self.model = None
    
    def is_available(self) -> bool:
        return self.model is not None
    
    def get_embedding(self, text: str) -> Optional[Any]:  # Returns np.ndarray when available
        if not self.model:
            return None
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32) if HAS_NUMPY else embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

class OllamaProvider(EmbeddingProvider):
    """Ollama embedding provider"""
    
    def __init__(self, model_name="nomic-embed-text", base_url="http://localhost:11434"):
        super().__init__()
        self.model_name = model_name
        self.base_url = base_url
        self.dimension = 768  # Nomic embedding dimension
    
    def is_available(self) -> bool:
        if not HAS_REQUESTS:
            return False
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_embedding(self, text: str) -> Optional[Any]:  # Returns np.ndarray when available
        if not HAS_REQUESTS:
            return None
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                embedding = np.array(data["embedding"], dtype=np.float32) if HAS_NUMPY else data["embedding"]
                return embedding
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
        return None

class OpenAIProvider(EmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self, api_key=None, model_name="text-embedding-ada-002"):
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.dimension = 1536  # Ada-002 dimension
    
    def is_available(self) -> bool:
        return bool(self.api_key and HAS_REQUESTS)
    
    def get_embedding(self, text: str) -> Optional[Any]:  # Returns np.ndarray when available
        if not self.is_available():
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model_name,
                "input": text
            }
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=data,
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                embedding = np.array(result["data"][0]["embedding"], dtype=np.float32) if HAS_NUMPY else result["data"][0]["embedding"]
                return embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
        return None

class VectorIndex:
    """Vector similarity search using HNSW"""
    
    def __init__(self, dimension: int, storage_path: Path):
        self.dimension = dimension
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.index_file = storage_path / "vectors.bin"
        self.metadata_file = storage_path / "metadata.json"
        
        self.index = None
        self.id_mapping = {}  # memory_id -> index_id
        self.reverse_mapping = {}  # index_id -> memory_id
        self.next_index_id = 0
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or load existing index"""
        if not HAS_HNSWLIB:
            logger.warning("HNSW vector search unavailable - install hnswlib")
            return
            
        self.index = hnswlib.Index(space='cosine', dim=self.dimension)
        
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                # Load existing index
                self.index.load_index(str(self.index_file))
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.id_mapping = metadata.get("id_mapping", {})
                    self.reverse_mapping = metadata.get("reverse_mapping", {})
                    self.next_index_id = metadata.get("next_index_id", 0)
                logger.info(f"Loaded vector index with {len(self.id_mapping)} vectors")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create new empty index"""
        if not HAS_HNSWLIB:
            return
        self.index.init_index(max_elements=100000, ef_construction=200, M=16)
        self.index.set_ef(50)
        self._save_metadata()
    
    def _save_metadata(self):
        """Save index metadata"""
        metadata = {
            "id_mapping": self.id_mapping,
            "reverse_mapping": self.reverse_mapping,
            "next_index_id": self.next_index_id,
            "dimension": self.dimension
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def add_vector(self, memory_id: str, vector: Any) -> bool:  # vector is np.ndarray when available
        """Add vector to index"""
        if not HAS_HNSWLIB or self.index is None:
            return False
        
        try:
            # Remove existing vector if it exists
            if memory_id in self.id_mapping:
                self.remove_vector(memory_id)
            
            index_id = self.next_index_id
            self.index.add_items(vector.reshape(1, -1), [index_id])
            
            self.id_mapping[memory_id] = index_id
            self.reverse_mapping[str(index_id)] = memory_id
            self.next_index_id += 1
            
            # Save periodically
            if self.next_index_id % 100 == 0:
                self.save()
            
            return True
        except Exception as e:
            logger.error(f"Error adding vector: {e}")
            return False
    
    def remove_vector(self, memory_id: str) -> bool:
        """Remove vector from index (logical deletion)"""
        if memory_id in self.id_mapping:
            index_id = self.id_mapping.pop(memory_id)
            self.reverse_mapping.pop(str(index_id), None)
            return True
        return False
    
    def search(self, query_vector: Any, k: int = 10) -> List[Tuple[str, float]]:  # query_vector is np.ndarray when available
        """Search for similar vectors"""
        if not HAS_HNSWLIB or self.index is None or len(self.id_mapping) == 0:
            return []
        
        try:
            labels, distances = self.index.knn_query(query_vector.reshape(1, -1), k=min(k, len(self.id_mapping)))
            
            results = []
            for label, distance in zip(labels[0], distances[0]):
                memory_id = self.reverse_mapping.get(str(label))
                if memory_id:
                    similarity = 1.0 - distance  # Convert distance to similarity
                    results.append((memory_id, similarity))
            
            return results
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def save(self):
        """Save index to disk"""
        if HAS_HNSWLIB and self.index is not None:
            try:
                self.index.save_index(str(self.index_file))
                self._save_metadata()
                logger.info(f"Saved vector index with {len(self.id_mapping)} vectors")
            except Exception as e:
                logger.error(f"Error saving index: {e}")

class UniversalMemoryService:
    """Core memory service with SQLite + vector search"""
    
    def __init__(self, storage_path: Optional[str] = None):
        # Storage setup
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".ai-memory"
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "memories.db"
        self.vector_path = self.storage_path / "vectors"
        
        # Initialize components
        self._lock = threading.Lock()
        self._init_database()
        self._init_embedding_provider()
        self._init_vector_index()
        
        logger.info(f"Memory service initialized: {self.storage_path}")
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    content_hash TEXT UNIQUE,
                    project TEXT,
                    category TEXT,
                    importance INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'active',
                    protection_level TEXT DEFAULT 'normal',
                    timestamp INTEGER,
                    access_count INTEGER DEFAULT 0,
                    last_accessed INTEGER,
                    tags TEXT,
                    metadata TEXT,
                    embedding_hash TEXT,
                    source TEXT,
                    source_url TEXT
                )
            """)
            
            # Create FTS table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
                USING fts5(content, content=memories, content_rowid=rowid)
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_content_hash ON memories(content_hash)")
            
            # Access tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT,
                    accessed_at INTEGER,
                    access_type TEXT,
                    context TEXT
                )
            """)
            
            conn.commit()
    
    def _init_embedding_provider(self):
        """Initialize embedding provider with fallbacks"""
        self.embedding_provider = None
        self.embedding_dimension = 384
        
        # Try providers in order of preference
        # SentenceTransformers first for best performance (10x faster, local, no server needed)
        providers = [
            ("sentence_transformers", SentenceTransformerProvider()),
            ("ollama", OllamaProvider()),
            ("openai", OpenAIProvider())
        ]
        
        for name, provider in providers:
            if provider.is_available():
                self.embedding_provider = provider
                self.embedding_dimension = provider.dimension
                logger.info(f"Using embedding provider: {name} (dim: {self.embedding_dimension})")
                break
        
        if not self.embedding_provider:
            logger.warning("No embedding provider available - semantic search disabled")
    
    def _init_vector_index(self):
        """Initialize vector search index"""
        self.vector_index = VectorIndex(self.embedding_dimension, self.vector_path)
    
    def _generate_id(self) -> str:
        """Generate unique memory ID"""
        timestamp = int(time.time() * 1000)
        return f"mem_{timestamp}_{hash(str(timestamp)) % 10000:04d}"
    
    def _hash_content(self, content: str) -> str:
        """Generate content hash for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _detect_project(self) -> Optional[str]:
        """Enhanced auto-detect current project from git or directory with GitHub integration"""
        try:
            import subprocess
            import os
            
            # Store current working directory
            original_cwd = os.getcwd()
            
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                                  capture_output=True, text=True, 
                                  cwd=original_cwd, 
                                  timeout=10)  # Add timeout for safety
            
            if result.returncode == 0:
                repo_path = Path(result.stdout.strip())
                
                # Try to get repository name from remote URL
                remote_result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                             capture_output=True, text=True, 
                                             cwd=str(repo_path),
                                             timeout=10)
                
                if remote_result.returncode == 0:
                    remote_url = remote_result.stdout.strip()
                    
                    # Parse GitHub URL formats
                    if 'github.com' in remote_url:
                        # Handle SSH format: git@github.com:user/repo.git
                        if remote_url.startswith('git@github.com:'):
                            # Extract user/repo part after colon
                            repo_part = remote_url.split(':', 1)[1].replace('.git', '')
                            # Return just the repo name (not user/repo)
                            if '/' in repo_part:
                                return repo_part.split('/')[-1]
                            return repo_part
                        
                        # Handle HTTPS format: https://github.com/user/repo.git
                        elif 'https://github.com/' in remote_url:
                            # Remove base URL and .git extension
                            repo_part = remote_url.replace('https://github.com/', '').replace('.git', '')
                            # Return just the repo name (not user/repo)
                            if '/' in repo_part:
                                return repo_part.split('/')[-1]
                            return repo_part
                    
                    # Handle other git remotes (GitLab, Bitbucket, etc.)
                    elif any(service in remote_url.lower() for service in ['gitlab.', 'bitbucket.', '.git']):
                        # Extract repo name from any git URL
                        repo_name = remote_url.split('/')[-1].replace('.git', '')
                        return repo_name
                
                # Fallback to directory name from git root
                return repo_path.name
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logger.debug(f"Git project detection failed: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error in git project detection: {e}")
        
        # Fall back to current directory name
        try:
            return Path.cwd().name
        except Exception:
            return "unknown-project"
    
    def _get_git_info(self) -> Dict[str, Any]:
        """Get comprehensive git repository information with improved error handling"""
        git_info = {
            'is_git_repo': False,
            'repo_root': None,
            'repo_name': None,
            'remote_url': None,
            'github_repo': None,
            'current_branch': None,
            'commit_hash': None
        }
        
        try:
            import subprocess
            import os
            
            # Store current working directory
            original_cwd = os.getcwd()
            
            # Check if in git repo
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                                  capture_output=True, text=True, 
                                  cwd=original_cwd, 
                                  timeout=10)
            
            if result.returncode == 0:
                git_info['is_git_repo'] = True
                git_info['repo_root'] = result.stdout.strip()
                repo_path = Path(git_info['repo_root'])
                git_info['repo_name'] = repo_path.name
                
                # Get remote URL with error handling
                try:
                    remote_result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                                 capture_output=True, text=True, 
                                                 cwd=str(repo_path),
                                                 timeout=10)
                    if remote_result.returncode == 0:
                        git_info['remote_url'] = remote_result.stdout.strip()
                        
                        # Parse GitHub repository
                        if 'github.com' in git_info['remote_url']:
                            remote_url = git_info['remote_url']
                            if remote_url.startswith('git@github.com:'):
                                # SSH format: git@github.com:user/repo.git
                                repo_path_part = remote_url.split(':', 1)[1].replace('.git', '')
                                git_info['github_repo'] = repo_path_part
                            elif 'https://github.com/' in remote_url:
                                # HTTPS format: https://github.com/user/repo.git
                                parts = remote_url.replace('https://github.com/', '').replace('.git', '')
                                git_info['github_repo'] = parts
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    logger.debug("Failed to get git remote URL")
                
                # Get current branch with error handling
                try:
                    branch_result = subprocess.run(['git', 'branch', '--show-current'],
                                                 capture_output=True, text=True, 
                                                 cwd=str(repo_path),
                                                 timeout=10)
                    if branch_result.returncode == 0:
                        git_info['current_branch'] = branch_result.stdout.strip()
                    else:
                        # Fallback for older git versions
                        branch_fallback = subprocess.run(['git', 'symbolic-ref', '--short', 'HEAD'],
                                                        capture_output=True, text=True,
                                                        cwd=str(repo_path),
                                                        timeout=10)
                        if branch_fallback.returncode == 0:
                            git_info['current_branch'] = branch_fallback.stdout.strip()
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    logger.debug("Failed to get git branch")
                
                # Get current commit hash with error handling
                try:
                    commit_result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                                 capture_output=True, text=True, 
                                                 cwd=str(repo_path),
                                                 timeout=10)
                    if commit_result.returncode == 0:
                        git_info['commit_hash'] = commit_result.stdout.strip()[:8]  # Short hash
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    logger.debug("Failed to get git commit hash")
                    
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
            logger.debug(f"Git info extraction failed: {e}")
        
        return git_info
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Auto-extract tags from content"""
        tags = []
        content_lower = content.lower()
        
        # Technical keywords
        tech_keywords = {
            'python', 'javascript', 'react', 'vue', 'angular', 'node', 'django', 'flask',
            'database', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
            'api', 'rest', 'graphql', 'authentication', 'oauth', 'jwt',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'performance', 'optimization', 'security', 'testing', 'debugging'
        }
        
        for keyword in tech_keywords:
            if keyword in content_lower:
                tags.append(keyword)
        
        return tags[:5]  # Limit to 5 auto-tags
    
    def _categorize_content(self, content: str) -> str:
        """Auto-categorize content based on patterns"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['solution', 'fix', 'resolved', 'works']):
            return 'solution'
        elif any(word in content_lower for word in ['pattern', 'approach', 'method', 'technique']):
            return 'pattern'  
        elif any(word in content_lower for word in ['decided', 'choice', 'selected', 'architecture']):
            return 'decision'
        elif any(word in content_lower for word in ['insight', 'learned', 'discovery', 'observation']):
            return 'insight'
        elif any(word in content_lower for word in ['reference', 'documentation', 'link', 'resource']):
            return 'reference'
        else:
            return 'insight'
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def store_memory(self, content: str, project: Optional[str] = None, 
                    category: Optional[str] = None, tags: Optional[List[str]] = None,
                    importance: int = 5, status: str = 'active',
                    protection_level: str = 'normal', source: Optional[str] = None,
                    source_url: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Store a new memory with deduplication"""
        
        with self._lock:
            # Generate hashes and IDs
            content_hash = self._hash_content(content)
            memory_id = self._generate_id()
            timestamp = int(time.time())
            
            # Auto-detect values
            if not project:
                project = self._detect_project()
            if not category:
                category = self._categorize_content(content)
            if not tags:
                tags = self._extract_tags_from_content(content)
            
            # Check for duplicates
            with self._get_connection() as conn:
                existing = conn.execute(
                    "SELECT id, access_count FROM memories WHERE content_hash = ?",
                    (content_hash,)
                ).fetchone()
                
                if existing:
                    # Update access count and return existing
                    conn.execute(
                        "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                        (timestamp, existing['id'])
                    )
                    conn.commit()
                    
                    # Log access
                    conn.execute(
                        "INSERT INTO access_log (memory_id, accessed_at, access_type, context) VALUES (?, ?, ?, ?)",
                        (existing['id'], timestamp, 'duplicate_store', f"Attempted duplicate: {content[:100]}...")
                    )
                    conn.commit()
                    
                    return {
                        'status': 'duplicate',
                        'id': existing['id'],
                        'message': 'Memory already exists'
                    }
                
                # Store new memory
                tags_json = json.dumps(tags) if tags else None
                metadata_json = json.dumps(metadata) if metadata else None
                
                conn.execute("""
                    INSERT INTO memories 
                    (id, content, content_hash, project, category, importance, status, protection_level,
                     timestamp, access_count, last_accessed, tags, metadata, source, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (memory_id, content, content_hash, project, category, importance, status,
                      protection_level, timestamp, 0, timestamp, tags_json, metadata_json, source, source_url))
                
                # Update FTS index
                conn.execute("INSERT INTO memories_fts(rowid, content) VALUES (last_insert_rowid(), ?)", (content,))
                conn.commit()
            
            # Generate and store embedding (synchronously)
            if self.embedding_provider:
                embedding = self.embedding_provider.get_embedding(content)
                if embedding is not None:
                    success = self.vector_index.add_vector(memory_id, embedding)
                    if success:
                        # Force immediate save of vector index
                        self.vector_index.save()
                        logger.info(f"Vector added for memory: {memory_id}")
                    else:
                        logger.warning(f"Failed to add vector for memory: {memory_id}")
            
            logger.info(f"Stored memory: {memory_id} [{category}] {content[:50]}...")
            
            return {
                'status': 'stored',
                'id': memory_id,
                'project': project,
                'category': category,
                'tags': tags
            }
    
    def search_memories(self, query: Optional[str] = None, project: Optional[str] = None,
                       category: Optional[str] = None, tags: Optional[List[str]] = None,
                       min_importance: int = 0, limit: int = 10, 
                       include_semantic: bool = True) -> List[Dict[str, Any]]:
        """Search memories using semantic + keyword search"""
        
        results = []
        
        with self._get_connection() as conn:
            # Build SQL query
            conditions = ["status NOT IN ('deleted', 'superseded')"]
            params = []
            
            if project:
                if project == "current":
                    project = self._detect_project()
                conditions.append("project = ?")
                params.append(project)
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if min_importance > 0:
                conditions.append("importance >= ?")
                params.append(min_importance)
            
            # Tag filtering
            if tags:
                for tag in tags:
                    conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
            
            where_clause = " AND ".join(conditions)
            
            if query:
                # Hybrid search: Semantic + Full-text with intelligent fallback
                semantic_results = {}
                fts_results = []
                
                # Try semantic search first (if available)
                if include_semantic and self.embedding_provider:
                    try:
                        query_embedding = self.embedding_provider.get_embedding(query)
                        if query_embedding is not None:
                            vector_matches = self.vector_index.search(query_embedding, limit * 2)
                            for memory_id, similarity in vector_matches:
                                semantic_results[memory_id] = similarity
                            logger.info(f"Semantic search found {len(semantic_results)} results")
                    except Exception as e:
                        logger.warning(f"Semantic search failed: {e}")
                
                # Always try full-text search as backup
                try:
                    fts_query = f"""
                        SELECT m.*, 
                               bm25(memories_fts) as fts_rank,
                               snippet(memories_fts, 0, '<mark>', '</mark>', '...', 32) as snippet
                        FROM memories_fts 
                        JOIN memories m ON m.rowid = memories_fts.rowid
                        WHERE memories_fts MATCH ? AND {where_clause}
                        ORDER BY bm25(memories_fts) DESC
                        LIMIT ?
                    """
                    
                    cursor = conn.execute(fts_query, [query] + params + [limit])
                    fts_results = cursor.fetchall()
                    logger.info(f"FTS search found {len(fts_results)} results")
                except Exception as e:
                    logger.warning(f"FTS search failed: {e}")
                
                # If both searches failed, try simple LIKE search
                if not semantic_results and not fts_results:
                    logger.info("Falling back to simple LIKE search")
                    like_query = f"""
                        SELECT * FROM memories 
                        WHERE content LIKE ? AND {where_clause}
                        ORDER BY importance DESC, timestamp DESC
                        LIMIT ?
                    """
                    cursor = conn.execute(like_query, [f"%{query}%"] + params + [limit])
                    fts_results = cursor.fetchall()
                
                # Combine results intelligently
                combined_results = {}
                
                # Add FTS results
                for row in fts_results:
                    memory_id = row['id']
                    semantic_score = semantic_results.get(memory_id, 0.0)
                    fts_rank = row['fts_rank'] if 'fts_rank' in row.keys() else 1.0
                    fts_score = 1.0 / (1.0 + abs(fts_rank))  # Convert BM25 to 0-1 score
                    combined_score = (semantic_score * 0.7) + (fts_score * 0.3) if semantic_score > 0 else fts_score
                    
                    combined_results[memory_id] = {
                        'memory': dict(row),
                        'score': float(combined_score),
                        'semantic_score': float(semantic_score),
                        'fts_score': float(fts_score)
                    }
                
                # Add purely semantic results not in FTS (if semantic search worked)
                if semantic_results:
                    for memory_id, similarity in semantic_results.items():
                        if memory_id not in combined_results and similarity > 0.3:  # Lower threshold for inclusion
                            try:
                                memory_row = conn.execute(f"SELECT * FROM memories WHERE id = ? AND {where_clause}", 
                                                        [memory_id] + params).fetchone()
                                if memory_row:
                                    combined_results[memory_id] = {
                                        'memory': dict(memory_row),
                                        'score': float(similarity * 0.7),
                                        'semantic_score': float(similarity),
                                        'fts_score': 0.0
                                    }
                            except Exception as e:
                                logger.warning(f"Failed to fetch semantic result {memory_id}: {e}")
                
                # Sort by combined score
                results = sorted(combined_results.values(), key=lambda x: x['score'], reverse=True)[:limit]
                
                logger.info(f"Combined search returned {len(results)} total results")
                
            else:
                # No query - return recent memories
                sql = f"""
                    SELECT * FROM memories 
                    WHERE {where_clause}
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?
                """
                cursor = conn.execute(sql, params + [limit])
                rows = cursor.fetchall()
                
                results = [{'memory': dict(row), 'score': 1.0, 'semantic_score': 0.0, 'fts_score': 0.0} 
                          for row in rows]
            
            # Update access counts
            timestamp = int(time.time())
            for result in results:
                memory_id = result['memory']['id']
                conn.execute(
                    "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                    (timestamp, memory_id)
                )
                # Log access
                conn.execute(
                    "INSERT INTO access_log (memory_id, accessed_at, access_type, context) VALUES (?, ?, ?, ?)",
                    (memory_id, timestamp, 'search', query or 'browse')
                )
            
            conn.commit()
        
        # Format results
        formatted_results = []
        for result in results:
            memory = result['memory']
            formatted_memory = {
                'id': memory['id'],
                'content': memory['content'],
                'project': memory['project'],
                'category': memory['category'],
                'importance': memory['importance'],
                'status': memory['status'],
                'protection_level': memory['protection_level'],
                'timestamp': memory['timestamp'],
                'access_count': memory['access_count'],
                'tags': json.loads(memory['tags']) if memory['tags'] else [],
                'metadata': json.loads(memory['metadata']) if memory['metadata'] else {},
                'source': memory['source'],
                'source_url': memory['source_url'],
                'similarity_score': float(result['semantic_score']),
                'relevance_score': float(result['score'])
            }
            formatted_results.append(formatted_memory)
        
        return formatted_results
    
    def get_context(self, relevant_to: Optional[str] = None, project: Optional[str] = None,
                   max_tokens: int = 4000, include_cross_project: bool = True,
                   protection_aware: bool = True) -> str:
        """Generate intelligent context for AI conversations"""
        
        context_parts = []
        used_tokens = 0
        
        # Estimate tokens (rough: 1 token ≈ 4 chars)
        def estimate_tokens(text: str) -> int:
            return len(text) // 4
        
        def add_to_context(title: str, content: str) -> bool:
            nonlocal used_tokens
            section = f"\n## {title}\n{content}\n"
            section_tokens = estimate_tokens(section)
            if used_tokens + section_tokens <= max_tokens:
                context_parts.append(section)
                used_tokens += section_tokens
                return True
            return False
        
        # Get relevant memories
        memories = []
        
        if relevant_to:
            # Search for relevant memories
            memories = self.search_memories(
                query=relevant_to,
                project=project,
                limit=20,
                include_semantic=True
            )
        else:
            # Get recent important memories
            memories = self.search_memories(
                project=project,
                min_importance=7,
                limit=15
            )
        
        # Categorize memories
        solutions = [m for m in memories if m['category'] == 'solution']
        patterns = [m for m in memories if m['category'] == 'pattern']
        decisions = [m for m in memories if m['category'] == 'decision']
        working_systems = [m for m in memories if m['status'] == 'working' and m['protection_level'] in ['high', 'critical']]
        failed_attempts = [m for m in memories if m['status'] == 'failed']
        
        # Build context sections in order of importance
        
        # Critical working systems (protected)
        if working_systems and protection_aware:
            working_content = "⚠️  **PROTECTED WORKING SYSTEMS (do not modify):**\n"
            for memory in working_systems[:3]:
                working_content += f"✅ {memory['content']}\n"
            add_to_context("WORKING SYSTEMS - DO NOT CHANGE", working_content)
        
        # Key solutions
        if solutions:
            solution_content = ""
            for i, memory in enumerate(solutions[:5], 1):
                importance_stars = "⭐" * memory['importance']
                solution_content += f"{i}. **{memory['project'] or 'General'}**: {memory['content']}\n"
                solution_content += f"   *Tags: {', '.join(memory['tags'])} | Importance: {importance_stars}*\n\n"
            if solution_content:
                add_to_context("Key Solutions", solution_content)
        
        # Important decisions
        if decisions:
            decision_content = ""
            for memory in decisions[:3]:
                decision_content += f"• **{memory['project'] or 'General'}**: {memory['content']}\n"
            if decision_content:
                add_to_context("Architectural Decisions", decision_content)
        
        # Useful patterns
        if patterns:
            pattern_content = ""
            for memory in patterns[:3]:
                pattern_content += f"• {memory['content']}\n"
            if pattern_content:
                add_to_context("Reusable Patterns", pattern_content)
        
        # Failed attempts (to avoid repetition)
        if failed_attempts and protection_aware:
            failed_content = "❌ **AVOID THESE (previously failed):**\n"
            for memory in failed_attempts[:3]:
                failed_content += f"• {memory['content']}\n"
            add_to_context("Failed Approaches", failed_content)
        
        # Cross-project insights
        if include_cross_project and project:
            cross_project_memories = self.search_memories(
                query=relevant_to,
                limit=5
            )
            cross_project_memories = [m for m in cross_project_memories if m['project'] != project]
            
            if cross_project_memories:
                cross_content = ""
                for memory in cross_project_memories[:3]:
                    cross_content += f"• **[{memory['project']}]**: {memory['content']}\n"
                if cross_content:
                    add_to_context("Related Experience from Other Projects", cross_content)
        
        # Assemble final context
        if not context_parts:
            return "No relevant context found in memory system."
        
        header = f"# AI Context for: {relevant_to or 'Current Work'}\n"
        if project:
            header += f"**Project**: {project}\n"
        header += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        context = header + "".join(context_parts)
        
        # Add usage note
        context += f"\n---\n*Context from Universal Memory System ({len(memories)} memories searched, ~{used_tokens} tokens)*"
        
        return context
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        with self._get_connection() as conn:
            # Overall stats
            total_memories = conn.execute("SELECT COUNT(*) as count FROM memories WHERE status != 'deleted'").fetchone()['count']
            total_projects = conn.execute("SELECT COUNT(DISTINCT project) as count FROM memories WHERE project IS NOT NULL AND status != 'deleted'").fetchone()['count']
            avg_importance = conn.execute("SELECT AVG(importance) as avg FROM memories WHERE status != 'deleted'").fetchone()['avg'] or 0
            total_accesses = conn.execute("SELECT SUM(access_count) as total FROM memories WHERE status != 'deleted'").fetchone()['total'] or 0
            
            # Project breakdown
            projects = conn.execute("""
                SELECT project, COUNT(*) as count, AVG(importance) as avg_importance,
                       MAX(timestamp) as last_activity
                FROM memories 
                WHERE project IS NOT NULL AND status != 'deleted'
                GROUP BY project 
                ORDER BY count DESC
            """).fetchall()
            
            # Category breakdown
            categories = conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM memories 
                WHERE category IS NOT NULL AND status != 'deleted'
                GROUP BY category 
                ORDER BY count DESC
            """).fetchall()
            
            # Most accessed
            most_accessed = conn.execute("""
                SELECT id, content, project, access_count, category
                FROM memories 
                WHERE status != 'deleted'
                ORDER BY access_count DESC 
                LIMIT 5
            """).fetchall()
            
            # Recent activity
            recent_memories = conn.execute("""
                SELECT id, content, project, timestamp, category
                FROM memories 
                WHERE status != 'deleted'
                ORDER BY timestamp DESC 
                LIMIT 5
            """).fetchall()
            
            return {
                'overall': {
                    'total_memories': total_memories,
                    'total_projects': total_projects,
                    'avg_importance': round(avg_importance, 1),
                    'total_accesses': total_accesses,
                    'embedding_provider': self.embedding_provider.__class__.__name__ if self.embedding_provider else None,
                    'vector_search_enabled': HAS_HNSWLIB and self.embedding_provider is not None,
                    'storage_path': str(self.storage_path)
                },
                'projects': {row['project']: {
                    'count': row['count'],
                    'avg_importance': round(row['avg_importance'], 1),
                    'last_activity': datetime.fromtimestamp(row['last_activity']).isoformat()
                } for row in projects},
                'categories': {row['category']: row['count'] for row in categories},
                'most_accessed': [{
                    'id': row['id'],
                    'content': row['content'][:100] + '...' if len(row['content']) > 100 else row['content'],
                    'project': row['project'],
                    'access_count': row['access_count'],
                    'category': row['category']
                } for row in most_accessed],
                'recent_memories': [{
                    'id': row['id'],
                    'content': row['content'][:100] + '...' if len(row['content']) > 100 else row['content'],
                    'project': row['project'],
                    'timestamp': datetime.fromtimestamp(row['timestamp']).isoformat(),
                    'category': row['category']
                } for row in recent_memories]
            }
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with statistics"""
        with self._get_connection() as conn:
            projects = conn.execute("""
                SELECT 
                    project,
                    COUNT(*) as memory_count,
                    AVG(importance) as avg_importance,
                    MAX(timestamp) as last_activity,
                    COUNT(CASE WHEN category = 'solution' THEN 1 END) as solutions,
                    COUNT(CASE WHEN category = 'pattern' THEN 1 END) as patterns,
                    COUNT(CASE WHEN category = 'decision' THEN 1 END) as decisions,
                    COUNT(CASE WHEN status = 'working' THEN 1 END) as working_systems,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_attempts
                FROM memories 
                WHERE project IS NOT NULL AND status != 'deleted'
                GROUP BY project 
                ORDER BY last_activity DESC
            """).fetchall()
            
            current_project = self._detect_project()
            
            return {
                'projects': [{
                    'name': row['project'],
                    'memory_count': row['memory_count'],
                    'avg_importance': round(row['avg_importance'], 1),
                    'last_activity': datetime.fromtimestamp(row['last_activity']).isoformat(),
                    'categories': {
                        'solutions': row['solutions'],
                        'patterns': row['patterns'],
                        'decisions': row['decisions'],
                        'working_systems': row['working_systems'],
                        'failed_attempts': row['failed_attempts']
                    }
                } for row in projects],
                'current_project': current_project
            }
    
    def find_related_memories(self, content: str, limit: int = 10, cross_project: bool = True) -> List[Dict[str, Any]]:
        """Find memories related to given content"""
        if not self.embedding_provider:
            # Fall back to keyword search
            return self.search_memories(query=content, limit=limit)
        
        # Get embedding for content
        query_embedding = self.embedding_provider.get_embedding(content)
        if query_embedding is None:
            return self.search_memories(query=content, limit=limit)
        
        # Vector search
        vector_results = self.vector_index.search(query_embedding, limit * 2)
        
        if not vector_results:
            return []
        
        # Get memory details
        memory_ids = [memory_id for memory_id, _ in vector_results]
        
        with self._get_connection() as conn:
            placeholders = ','.join('?' * len(memory_ids))
            sql = f"""
                SELECT * FROM memories 
                WHERE id IN ({placeholders}) AND status != 'deleted'
            """
            
            if not cross_project:
                current_project = self._detect_project()
                sql += " AND project = ?"
                memory_ids.append(current_project)
            
            rows = conn.execute(sql, memory_ids).fetchall()
            
            # Create mapping and sort by similarity
            memory_map = {row['id']: dict(row) for row in rows}
            
            results = []
            for memory_id, similarity in vector_results:
                if memory_id in memory_map and similarity > 0.3:  # Threshold for relevance
                    memory = memory_map[memory_id]
                    results.append({
                        'id': memory['id'],
                        'content': memory['content'],
                        'project': memory['project'],
                        'category': memory['category'],
                        'importance': memory['importance'],
                        'tags': json.loads(memory['tags']) if memory['tags'] else [],
                        'similarity_score': similarity,
                        'timestamp': memory['timestamp']
                    })
            
            return results[:limit]
    
    def cleanup_memories(self, remove_duplicates: bool = False, remove_old: bool = False,
                        days_threshold: int = 365, remove_unused: bool = False,
                        access_threshold: int = 0) -> Dict[str, int]:
        """Clean up memories based on various criteria"""
        
        removed_count = {'duplicates': 0, 'old': 0, 'unused': 0}
        
        with self._get_connection() as conn:
            if remove_duplicates:
                # Find and remove duplicate content (keep the most accessed one)
                duplicates = conn.execute("""
                    SELECT content_hash, GROUP_CONCAT(id) as ids, GROUP_CONCAT(access_count) as counts
                    FROM memories 
                    WHERE status != 'deleted'
                    GROUP BY content_hash 
                    HAVING COUNT(*) > 1
                """).fetchall()
                
                for row in duplicates:
                    ids = row['ids'].split(',')
                    counts = list(map(int, row['counts'].split(',')))
                    
                    # Keep the most accessed one
                    max_index = counts.index(max(counts))
                    keep_id = ids[max_index]
                    
                    # Mark others as deleted
                    delete_ids = [id for i, id in enumerate(ids) if i != max_index]
                    for delete_id in delete_ids:
                        conn.execute("UPDATE memories SET status = 'deleted' WHERE id = ?", (delete_id,))
                        removed_count['duplicates'] += 1
            
            if remove_old:
                # Remove memories older than threshold
                cutoff_timestamp = int(time.time()) - (days_threshold * 24 * 3600)
                result = conn.execute("""
                    UPDATE memories 
                    SET status = 'deleted' 
                    WHERE timestamp < ? AND status != 'deleted' AND protection_level = 'normal'
                """, (cutoff_timestamp,))
                removed_count['old'] = result.rowcount
            
            if remove_unused:
                # Remove memories with low access counts
                result = conn.execute("""
                    UPDATE memories 
                    SET status = 'deleted' 
                    WHERE access_count <= ? AND status != 'deleted' AND protection_level = 'normal'
                """, (access_threshold,))
                removed_count['unused'] = result.rowcount
            
            conn.commit()
        
        # Clean up vector index for deleted memories
        with self._get_connection() as conn:
            deleted_ids = conn.execute("SELECT id FROM memories WHERE status = 'deleted'").fetchall()
            for row in deleted_ids:
                self.vector_index.remove_vector(row['id'])
        
        self.vector_index.save()
        
        logger.info(f"Cleanup complete: {removed_count}")
        return removed_count
    
    def export_memories(self, format: str = 'json', project: Optional[str] = None,
                       category: Optional[str] = None, limit: Optional[int] = None) -> str:
        """Export memories in various formats"""
        
        memories = self.search_memories(
            project=project,
            category=category,
            limit=limit or 10000
        )
        
        if format == 'json':
            return json.dumps(memories, indent=2, default=str)
        
        elif format == 'markdown':
            output = f"# Memory Export\n\n"
            output += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"**Total Memories**: {len(memories)}\n\n"
            
            # Group by category
            categories = {}
            for memory in memories:
                cat = memory['category'] or 'uncategorized'
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(memory)
            
            for category, mems in categories.items():
                output += f"## {category.title()}\n\n"
                for memory in mems:
                    tags = ', '.join(memory['tags'])
                    importance = '⭐' * memory['importance']
                    
                    output += f"### {memory['project'] or 'General'}\n"
                    output += f"**Content**: {memory['content']}\n"
                    output += f"**Tags**: {tags}\n"
                    output += f"**Importance**: {importance}\n"
                    output += f"**Date**: {datetime.fromtimestamp(memory['timestamp']).strftime('%Y-%m-%d')}\n\n"
            
            return output
        
        elif format == 'chatgpt':
            output = "Here's my relevant experience from previous projects:\n\n"
            
            solutions = [m for m in memories if m['category'] == 'solution']
            patterns = [m for m in memories if m['category'] == 'pattern']
            decisions = [m for m in memories if m['category'] == 'decision']
            
            if solutions:
                output += "SOLUTIONS:\n"
                for memory in solutions[:5]:
                    output += f"• {memory['content']}\n"
                output += "\n"
            
            if patterns:
                output += "PATTERNS:\n"
                for memory in patterns[:3]:
                    output += f"• {memory['content']}\n"
                output += "\n"
            
            if decisions:
                output += "DECISIONS:\n"
                for memory in decisions[:3]:
                    output += f"• {memory['content']}\n"
                output += "\n"
            
            output += "Current question: [Your question here]"
            return output
        
        elif format == 'claude':
            output = "I'm working on a project and have some relevant context from my previous work:\n\n"
            
            categories = {}
            for memory in memories:
                cat = memory['category'] or 'insights'
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(memory)
            
            for category, mems in categories.items():
                output += f"## {category.title()}:\n"
                for memory in mems[:3]:
                    output += f"- {memory['content']}\n"
                output += "\n"
            
            output += "Current question: [Your question here]"
            return output
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if backup_path:
            backup_file = Path(backup_path) / f"memory_backup_{timestamp}.db"
        else:
            backup_dir = self.storage_path / "backups"
            backup_dir.mkdir(exist_ok=True)
            backup_file = backup_dir / f"memory_backup_{timestamp}.db"
        
        # Copy database
        import shutil
        shutil.copy2(self.db_path, backup_file)
        
        # Save vector index
        vector_backup = backup_file.parent / f"vectors_backup_{timestamp}"
        vector_backup.mkdir(exist_ok=True)
        shutil.copytree(self.vector_path, vector_backup, dirs_exist_ok=True)
        
        logger.info(f"Backup created: {backup_file}")
        return str(backup_file)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            'status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Database check
            with self._get_connection() as conn:
                conn.execute("SELECT COUNT(*) FROM memories").fetchone()
            health['checks']['database'] = 'ok'
        except Exception as e:
            health['checks']['database'] = 'error'
            health['errors'].append(f"Database error: {e}")
            health['status'] = 'unhealthy'
        
        # Embedding provider check
        if self.embedding_provider:
            if self.embedding_provider.is_available():
                health['checks']['embeddings'] = 'ok'
            else:
                health['checks']['embeddings'] = 'warning'
                health['warnings'].append("Embedding provider not available")
        else:
            health['checks']['embeddings'] = 'warning'
            health['warnings'].append("No embedding provider configured")
        
        # Vector index check
        if HAS_HNSWLIB and self.vector_index:
            health['checks']['vector_index'] = 'ok'
        else:
            health['checks']['vector_index'] = 'warning'
            health['warnings'].append("Vector search not available")
        
        # Storage check
        if self.storage_path.exists() and os.access(self.storage_path, os.R_OK | os.W_OK):
            health['checks']['storage'] = 'ok'
        else:
            health['checks']['storage'] = 'error'
            health['errors'].append("Storage directory not accessible")
            health['status'] = 'unhealthy'
        
        # Set overall status
        if health['errors']:
            health['status'] = 'unhealthy'
        elif health['warnings']:
            health['status'] = 'degraded'
        
        return health

# Service singleton
_memory_service = None

def get_memory_service(storage_path: Optional[str] = None) -> UniversalMemoryService:
    """Get or create memory service singleton"""
    global _memory_service
    if _memory_service is None:
        _memory_service = UniversalMemoryService(storage_path)
    return _memory_service

if __name__ == "__main__":
    # Simple test
    service = UniversalMemoryService()
    
    # Test storing a memory
    result = service.store_memory(
        content="Test memory content for the Universal AI Memory System",
        project="test-project",
        tags=["test", "memory"],
        importance=8
    )
    print(f"Store result: {result}")
    
    # Test searching
    results = service.search_memories(query="memory system", limit=5)
    print(f"Search results: {len(results)}")
    for result in results:
        print(f"  - {result['content'][:50]}... (score: {result['relevance_score']:.3f})")
    
    # Test getting context
    context = service.get_context(relevant_to="memory management")
    print(f"Context generated ({len(context)} chars)")
    
    # Test statistics
    stats = service.get_statistics()
    print(f"Statistics: {stats['overall']['total_memories']} memories, {stats['overall']['total_projects']} projects")