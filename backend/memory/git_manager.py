"""
Git Manager module for ScribeNet.
Handles version control operations for book projects.
"""

import git
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class GitManager:
    """
    Git repository manager for versioning book content.
    
    Each project gets its own git repository for tracking changes,
    branching experimental rewrites, and enabling rollbacks.
    """
    
    def __init__(self, projects_base_path: str = "data/projects"):
        """
        Initialize Git manager.
        
        Args:
            projects_base_path: Base directory for project repositories
        """
        self.base_path = Path(projects_base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_repo_path(self, project_id: str) -> Path:
        """Get the repository path for a project."""
        return self.base_path / f"project-{project_id}"
    
    def _ensure_repo(self, project_id: str) -> git.Repo:
        """
        Ensure git repository exists for project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            git.Repo instance
        """
        repo_path = self._get_repo_path(project_id)
        
        if (repo_path / ".git").exists():
            return git.Repo(repo_path)
        
        # Initialize new repository
        repo_path.mkdir(parents=True, exist_ok=True)
        repo = git.Repo.init(repo_path)
        
        # Create initial structure
        (repo_path / "chapters").mkdir(exist_ok=True)
        (repo_path / "drafts").mkdir(exist_ok=True)
        (repo_path / "metadata").mkdir(exist_ok=True)
        
        # Create .gitignore
        gitignore_path = repo_path / ".gitignore"
        gitignore_path.write_text("*.tmp\n*.swp\n.DS_Store\n")
        
        # Initial commit
        repo.index.add([".gitignore"])
        repo.index.commit("Initial commit")
        
        return repo
    
    # ==================== Project Initialization ====================
    
    def init_project(
        self,
        project_id: str,
        title: str,
        genre: str,
        vision_document: str = ""
    ) -> Dict[str, Any]:
        """
        Initialize a git repository for a new project.
        
        Args:
            project_id: Project identifier
            title: Project title
            genre: Project genre
            vision_document: Initial vision/planning document
            
        Returns:
            Repository info dictionary
        """
        repo = self._ensure_repo(project_id)
        repo_path = self._get_repo_path(project_id)
        
        # Create metadata files
        metadata = {
            "project_id": project_id,
            "title": title,
            "genre": genre,
            "created_at": datetime.now().isoformat()
        }
        
        metadata_path = repo_path / "metadata" / "project.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        if vision_document:
            vision_path = repo_path / "metadata" / "vision_document.md"
            vision_path.write_text(vision_document)
            repo.index.add(["metadata/vision_document.md"])
        
        repo.index.add(["metadata/project.json"])
        repo.index.commit(f"Initialize project: {title}")
        
        return {
            "project_id": project_id,
            "repo_path": str(repo_path),
            "current_branch": repo.active_branch.name,
            "commit_count": len(list(repo.iter_commits()))
        }
    
    # ==================== Chapter Operations ====================
    
    def save_chapter(
        self,
        project_id: str,
        chapter_number: int,
        title: str,
        content: str,
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a chapter and commit to git.
        
        Args:
            project_id: Project identifier
            chapter_number: Chapter number
            title: Chapter title
            content: Chapter content
            commit_message: Optional custom commit message
            
        Returns:
            Commit info dictionary
        """
        repo = self._ensure_repo(project_id)
        repo_path = self._get_repo_path(project_id)
        
        # Create chapter file
        chapter_filename = f"chapter_{chapter_number:02d}.md"
        chapter_path = repo_path / "chapters" / chapter_filename
        
        # Add frontmatter
        full_content = f"""---
chapter: {chapter_number}
title: {title}
updated: {datetime.now().isoformat()}
---

# Chapter {chapter_number}: {title}

{content}
"""
        
        chapter_path.write_text(full_content)
        
        # Stage and commit
        repo.index.add([f"chapters/{chapter_filename}"])
        
        if not commit_message:
            commit_message = f"Update Chapter {chapter_number}: {title}"
        
        commit = repo.index.commit(commit_message)
        
        return {
            "project_id": project_id,
            "chapter_number": chapter_number,
            "commit_hash": commit.hexsha,
            "commit_message": commit_message,
            "timestamp": commit.committed_datetime.isoformat()
        }
    
    def save_draft(
        self,
        project_id: str,
        chapter_number: int,
        version: int,
        content: str,
        agent_type: str = "writer"
    ) -> Dict[str, Any]:
        """
        Save a draft version without committing to main.
        
        Args:
            project_id: Project identifier
            chapter_number: Chapter number
            version: Draft version number
            content: Draft content
            agent_type: Agent that created this draft
            
        Returns:
            Draft info dictionary
        """
        repo = self._ensure_repo(project_id)
        repo_path = self._get_repo_path(project_id)
        
        # Create draft directory for this chapter
        draft_dir = repo_path / "drafts" / f"chapter_{chapter_number:02d}"
        draft_dir.mkdir(parents=True, exist_ok=True)
        
        # Save draft
        draft_filename = f"draft_v{version}.md"
        draft_path = draft_dir / draft_filename
        
        draft_content = f"""---
chapter: {chapter_number}
version: {version}
agent: {agent_type}
created: {datetime.now().isoformat()}
---

{content}
"""
        
        draft_path.write_text(draft_content)
        
        # Commit draft
        repo.index.add([f"drafts/chapter_{chapter_number:02d}/{draft_filename}"])
        commit = repo.index.commit(f"Draft: Chapter {chapter_number} v{version} by {agent_type}")
        
        return {
            "project_id": project_id,
            "chapter_number": chapter_number,
            "version": version,
            "draft_path": str(draft_path),
            "commit_hash": commit.hexsha
        }
    
    def save_outline(
        self,
        project_id: str,
        outline_content: str
    ) -> Dict[str, Any]:
        """
        Save project outline.
        
        Args:
            project_id: Project identifier
            outline_content: Outline content
            
        Returns:
            Commit info
        """
        repo = self._ensure_repo(project_id)
        repo_path = self._get_repo_path(project_id)
        
        outline_path = repo_path / "outline.md"
        outline_path.write_text(outline_content)
        
        repo.index.add(["outline.md"])
        commit = repo.index.commit("Update project outline")
        
        return {
            "project_id": project_id,
            "commit_hash": commit.hexsha,
            "timestamp": commit.committed_datetime.isoformat()
        }
    
    def save_story_bible(
        self,
        project_id: str,
        story_bible: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save story bible to git.
        
        Args:
            project_id: Project identifier
            story_bible: Story bible dictionary
            
        Returns:
            Commit info
        """
        repo = self._ensure_repo(project_id)
        repo_path = self._get_repo_path(project_id)
        
        bible_path = repo_path / "story_bible.json"
        bible_path.write_text(json.dumps(story_bible, indent=2))
        
        repo.index.add(["story_bible.json"])
        commit = repo.index.commit("Update story bible")
        
        return {
            "project_id": project_id,
            "commit_hash": commit.hexsha,
            "timestamp": commit.committed_datetime.isoformat()
        }
    
    # ==================== Version Control Operations ====================
    
    def get_history(
        self,
        project_id: str,
        max_count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get commit history for a project.
        
        Args:
            project_id: Project identifier
            max_count: Maximum number of commits to return
            
        Returns:
            List of commit info dictionaries
        """
        repo = self._ensure_repo(project_id)
        
        commits = []
        for commit in repo.iter_commits(max_count=max_count):
            commits.append({
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:7],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "timestamp": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files)
            })
        
        return commits
    
    def get_file_history(
        self,
        project_id: str,
        file_path: str,
        max_count: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get history for a specific file.
        
        Args:
            project_id: Project identifier
            file_path: Relative path to file
            max_count: Maximum number of commits
            
        Returns:
            List of commits affecting this file
        """
        repo = self._ensure_repo(project_id)
        
        commits = []
        for commit in repo.iter_commits(paths=file_path, max_count=max_count):
            commits.append({
                "hash": commit.hexsha,
                "message": commit.message.strip(),
                "timestamp": commit.committed_datetime.isoformat()
            })
        
        return commits
    
    def create_branch(
        self,
        project_id: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a new branch for experimental rewrites.
        
        Args:
            project_id: Project identifier
            branch_name: New branch name
            from_branch: Branch to branch from
            
        Returns:
            Branch info
        """
        repo = self._ensure_repo(project_id)
        
        # Ensure we're on the source branch
        if from_branch in repo.heads:
            repo.heads[from_branch].checkout()
        
        # Create new branch
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        
        return {
            "project_id": project_id,
            "branch_name": branch_name,
            "from_branch": from_branch,
            "current_branch": repo.active_branch.name
        }
    
    def switch_branch(
        self,
        project_id: str,
        branch_name: str
    ) -> Dict[str, Any]:
        """
        Switch to a different branch.
        
        Args:
            project_id: Project identifier
            branch_name: Branch to switch to
            
        Returns:
            Branch info
        """
        repo = self._ensure_repo(project_id)
        
        if branch_name in repo.heads:
            repo.heads[branch_name].checkout()
        else:
            raise ValueError(f"Branch '{branch_name}' does not exist")
        
        return {
            "project_id": project_id,
            "current_branch": repo.active_branch.name
        }
    
    def list_branches(self, project_id: str) -> List[str]:
        """
        List all branches for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of branch names
        """
        repo = self._ensure_repo(project_id)
        return [head.name for head in repo.heads]
    
    def rollback(
        self,
        project_id: str,
        commit_hash: str
    ) -> Dict[str, Any]:
        """
        Rollback to a specific commit.
        
        Args:
            project_id: Project identifier
            commit_hash: Commit hash to rollback to
            
        Returns:
            Rollback info
        """
        repo = self._ensure_repo(project_id)
        
        # Reset to commit
        repo.git.reset('--hard', commit_hash)
        
        return {
            "project_id": project_id,
            "rolled_back_to": commit_hash,
            "current_branch": repo.active_branch.name
        }
    
    def get_diff(
        self,
        project_id: str,
        commit_hash_a: str,
        commit_hash_b: str
    ) -> str:
        """
        Get diff between two commits.
        
        Args:
            project_id: Project identifier
            commit_hash_a: First commit
            commit_hash_b: Second commit
            
        Returns:
            Diff text
        """
        repo = self._ensure_repo(project_id)
        
        commit_a = repo.commit(commit_hash_a)
        commit_b = repo.commit(commit_hash_b)
        
        return commit_a.diff(commit_b, create_patch=True)
    
    # ==================== Tag Operations ====================
    
    def create_tag(
        self,
        project_id: str,
        tag_name: str,
        message: str = ""
    ) -> Dict[str, Any]:
        """
        Create a tag (e.g., for releases like 'draft-1.0', 'final-1.0').
        
        Args:
            project_id: Project identifier
            tag_name: Tag name
            message: Optional tag message
            
        Returns:
            Tag info
        """
        repo = self._ensure_repo(project_id)
        
        tag = repo.create_tag(tag_name, message=message)
        
        return {
            "project_id": project_id,
            "tag_name": tag_name,
            "commit_hash": tag.commit.hexsha
        }
    
    def list_tags(self, project_id: str) -> List[str]:
        """
        List all tags for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of tag names
        """
        repo = self._ensure_repo(project_id)
        return [tag.name for tag in repo.tags]
    
    # ==================== Export Operations ====================
    
    def export_content(
        self,
        project_id: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export all content from repository.
        
        Args:
            project_id: Project identifier
            output_path: Optional output path
            
        Returns:
            Path to exported content
        """
        repo_path = self._get_repo_path(project_id)
        
        if output_path is None:
            output_path = self.base_path / f"export-{project_id}"
        
        # Copy repository content (excluding .git)
        import shutil
        if output_path.exists():
            shutil.rmtree(output_path)
        
        shutil.copytree(
            repo_path,
            output_path,
            ignore=shutil.ignore_patterns('.git', '*.tmp')
        )
        
        return output_path
