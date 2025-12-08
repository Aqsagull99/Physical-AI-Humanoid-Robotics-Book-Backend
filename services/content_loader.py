import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.logging import logger
from core.config import settings

class ContentLoader:
    """
    Service to load and process book content from the Docusaurus site
    """

    def __init__(self, content_path: Optional[str] = None):
        self.content_path = content_path or settings.book_content_path
        self.content = []

    def load_content(self) -> List[Dict[str, Any]]:
        """
        Load content from the Docusaurus site
        """
        logger.info(f"Loading content from {self.content_path}")

        # Only check the specific content path provided (should be my_book_content)
        content_sources = [self.content_path]

        for source in content_sources:
            if os.path.exists(source):
                logger.info(f"Found content source at {source}")
                self.content = self._extract_content_from_directory(source)
                # Only use sample content if no markdown files were found
                if not self.content:
                    logger.warning(f"No markdown content found at {source}, using sample content")
                    self.content = self._get_sample_content()
                break
        else:
            logger.warning(f"No content found at {self.content_path}, using sample content")
            self.content = self._get_sample_content()

        logger.info(f"Loaded {len(self.content)} content chunks")
        return self.content

    def _extract_content_from_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        Extract content from a directory structure
        """
        content_chunks = []

        # Walk through the directory to find markdown files
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.md', '.mdx')):
                    file_path = os.path.join(root, file)
                    try:
                        chunks = self._extract_content_from_file(file_path)
                        content_chunks.extend(chunks)
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {str(e)}")

        return content_chunks

    def _extract_content_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract content from a single markdown file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple chunking - split by paragraphs or sections
        chunks = self._chunk_content(content, file_path)

        return chunks

    def _chunk_content(self, content: str, source_file: str) -> List[Dict[str, Any]]:
        """
        Split content into chunks with enhanced metadata
        """
        chunks = []

        # Extract document title from the first header if available
        title = self._extract_title(content)

        # Split content into paragraphs
        paragraphs = content.split('\n\n')

        import uuid
        for i, paragraph in enumerate(paragraphs):
            # Skip empty paragraphs
            if paragraph.strip():
                # Skip if it's just a header line
                if not paragraph.strip().startswith('#'):
                    # Extract section if available
                    section = self._extract_section(content, paragraph.strip())
                    # Create the full chunk with content in metadata for Qdrant
                    chunk = {
                        'id': str(uuid.uuid4()),  # Generate a proper UUID instead of string ID
                        'content': paragraph.strip(),
                        'source_file': source_file,
                        'chunk_index': i,
                        'metadata': {
                            'file_path': source_file,
                            'chunk_id': i,
                            'type': 'paragraph',
                            'title': title,
                            'section': section,
                            'page_reference': self._extract_page_reference(paragraph),
                            'content': paragraph.strip()  # Include the actual content in metadata for Qdrant
                        }
                    }
                    chunks.append(chunk)

        return chunks

    def _extract_title(self, content: str) -> str:
        """
        Extract the document title from the content (first H1 header)
        """
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('# '):
                return line.strip()[2:]  # Remove '# ' prefix
        return 'Unknown Title'

    def _extract_section(self, content: str, current_paragraph: str) -> str:
        """
        Extract section information from content relative to the current paragraph
        """
        # Split content into lines to find the closest section header above this paragraph
        lines = content.split('\n')

        # Find the position of the current paragraph in the content
        paragraph_pos = content.find(current_paragraph.strip())
        if paragraph_pos == -1:
            return 'General Section'

        # Look for the most recent section header before this paragraph
        current_pos = 0
        section = 'General Section'

        for line in lines:
            line_stripped = line.strip()
            if current_pos >= paragraph_pos:
                break
            if line_stripped.startswith('## '):
                section = line_stripped[3:]  # Remove '## ' prefix
            elif line_stripped.startswith('### '):
                section = line_stripped[4:]  # Remove '### ' prefix
            current_pos += len(line) + 1  # +1 for the newline character

        return section

    def _extract_page_reference(self, paragraph: str) -> Optional[str]:
        """
        Extract page reference if available in the paragraph
        """
        # This is a placeholder - in a real implementation, you might extract
        # page numbers or section references from the content
        import re
        page_pattern = r'page\s+(\d+)|p\.(\d+)'
        match = re.search(page_pattern, paragraph, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2)
        return None

    def _get_sample_content(self) -> List[Dict[str, Any]]:
        """
        Return sample content for testing purposes
        """
        import uuid
        return [
            {
                'id': str(uuid.uuid4()),  # Generate a proper UUID
                'content': 'This is sample content about Physical AI and Humanoid Robotics. Physical AI is an interdisciplinary field combining robotics, machine learning, and biomechanics.',
                'source_file': 'sample.md',
                'chunk_index': 0,
                'metadata': {
                    'file_path': 'sample.md',
                    'chunk_id': 0,
                    'type': 'paragraph',
                    'content': 'This is sample content about Physical AI and Humanoid Robotics. Physical AI is an interdisciplinary field combining robotics, machine learning, and biomechanics.'  # Include content in metadata
                }
            },
            {
                'id': str(uuid.uuid4()),  # Generate a proper UUID
                'content': 'Humanoid robots are designed to resemble and mimic human behavior and appearance. They often feature articulated limbs and a head with sensory capabilities.',
                'source_file': 'sample.md',
                'chunk_index': 1,
                'metadata': {
                    'file_path': 'sample.md',
                    'chunk_id': 1,
                    'type': 'paragraph',
                    'content': 'Humanoid robots are designed to resemble and mimic human behavior and appearance. They often feature articulated limbs and a head with sensory capabilities.'  # Include content in metadata
                }
            }
        ]

    def get_content(self) -> List[Dict[str, Any]]:
        """
        Get the loaded content
        """
        return self.content

# Lazy singleton instance
_content_loader_instance = None

def get_content_loader():
    """
    Get the content loader instance, creating it if it doesn't exist
    """
    global _content_loader_instance
    if _content_loader_instance is None:
        _content_loader_instance = ContentLoader()
    return _content_loader_instance