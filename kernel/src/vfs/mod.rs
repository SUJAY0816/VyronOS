// ==============================================================================
// VYRON Micro-OS - Capability-Based Virtual Filesystem (VFS)
// Layer 11: Capability File System Architecture
//
// Provenance & Attribution:
// - Origin: Adapted from EuraliOS VFS & Server abstractions (https://github.com/bendudson/euralios)
// - Authors: Ben Dudson (EuraliOS)
// - License: MIT License (https://opensource.org/licenses/MIT)
//
// Subsystem Description:
// Implements capability-safe, handle-based virtual files and directories.
// Nodes can represent static memory files, dynamic devices, or IPC channel endpoints.
// ==============================================================================

use std::collections::BTreeMap;
use std::sync::{Arc, RwLock};

pub const O_READ: u32 = 1 << 0;
pub const O_WRITE: u32 = 1 << 1;
pub const O_EXEC: u32 = 1 << 2;
pub const O_CREATE: u32 = 1 << 3;

/// Trait for file-like objects capable of streaming I/O
pub trait FileLike: Send + Sync {
    fn read(&self, offset: usize, buffer: &mut [u8]) -> Result<usize, &'static str>;
    fn write(&mut self, offset: usize, buffer: &[u8]) -> Result<usize, &'static str>;
    fn size(&self) -> usize;
}

/// Trait for directory-like objects supporting path resolution
pub trait DirLike: Send + Sync {
    fn get_file(&self, name: &str) -> Option<Arc<RwLock<dyn FileLike>>>;
    fn get_dir(&self, name: &str) -> Option<Arc<RwLock<dyn DirLike>>>;
    fn list_entries(&self) -> Vec<String>;
}

/// In-Memory RAM File Node
#[derive(Debug, Default)]
pub struct MemoryFile {
    pub data: Vec<u8>,
}

impl MemoryFile {
    pub fn new(initial_data: &[u8]) -> Self {
        Self {
            data: initial_data.to_vec(),
        }
    }
}

impl FileLike for MemoryFile {
    fn read(&self, offset: usize, buffer: &mut [u8]) -> Result<usize, &'static str> {
        if offset >= self.data.len() {
            return Ok(0); // EOF
        }
        let available = self.data.len() - offset;
        let to_read = std::cmp::min(buffer.len(), available);
        buffer[..to_read].copy_from_slice(&self.data[offset..offset + to_read]);
        Ok(to_read)
    }

    fn write(&mut self, offset: usize, buffer: &[u8]) -> Result<usize, &'static str> {
        let end = offset + buffer.len();
        if end > self.data.len() {
            self.data.resize(end, 0);
        }
        self.data[offset..end].copy_from_slice(buffer);
        Ok(buffer.len())
    }

    fn size(&self) -> usize {
        self.data.len()
    }
}

/// In-Memory Directory Node
#[derive(Default)]
pub struct MemoryDirectory {
    pub files: BTreeMap<String, Arc<RwLock<dyn FileLike>>>,
    pub subdirs: BTreeMap<String, Arc<RwLock<dyn DirLike>>>,
}

impl MemoryDirectory {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_file(&mut self, name: &str, file: Arc<RwLock<dyn FileLike>>) {
        self.files.insert(name.to_string(), file);
    }

    pub fn add_dir(&mut self, name: &str, dir: Arc<RwLock<dyn DirLike>>) {
        self.subdirs.insert(name.to_string(), dir);
    }
}

impl DirLike for MemoryDirectory {
    fn get_file(&self, name: &str) -> Option<Arc<RwLock<dyn FileLike>>> {
        self.files.get(name).cloned()
    }

    fn get_dir(&self, name: &str) -> Option<Arc<RwLock<dyn DirLike>>> {
        self.subdirs.get(name).cloned()
    }

    fn list_entries(&self) -> Vec<String> {
        let mut entries = Vec::new();
        for k in self.subdirs.keys() {
            entries.push(format!("{}/", k));
        }
        for k in self.files.keys() {
            entries.push(k.clone());
        }
        entries
    }
}

/// Capability VFS Root Manager
pub struct VfsRoot {
    pub root: Arc<RwLock<MemoryDirectory>>,
}

impl Default for VfsRoot {
    fn default() -> Self {
        Self::new()
    }
}

impl VfsRoot {
    pub fn new() -> Self {
        let root = Arc::new(RwLock::new(MemoryDirectory::new()));
        Self { root }
    }

    pub fn populate_default_hierarchy(&self) {
        let mut root = self.root.write().unwrap();

        // Create /dev, /etc, /proc directories
        let dev = Arc::new(RwLock::new(MemoryDirectory::new()));
        let etc = Arc::new(RwLock::new(MemoryDirectory::new()));
        let proc_dir = Arc::new(RwLock::new(MemoryDirectory::new()));

        // Add /etc/os-release
        let os_release_content = b"NAME=\"VyronOS\"\nVERSION=\"7.0.0\"\nID=vyron\nID_LIKE=debian\n";
        let os_release_file = Arc::new(RwLock::new(MemoryFile::new(os_release_content)));
        etc.write().unwrap().add_file("os-release", os_release_file);

        // Add /dev/null
        let null_dev = Arc::new(RwLock::new(MemoryFile::new(&[])));
        dev.write().unwrap().add_file("null", null_dev);

        root.add_dir("dev", dev);
        root.add_dir("etc", etc);
        root.add_dir("proc", proc_dir);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vfs_memory_file_io() {
        let mut file = MemoryFile::new(b"Hello VyronOS!");
        assert_eq!(file.size(), 14);

        let mut buf = [0u8; 5];
        let bytes_read = file.read(6, &mut buf).unwrap();
        assert_eq!(bytes_read, 5);
        assert_eq!(&buf, b"Vyron");

        file.write(6, b"World!!").unwrap();
        assert_eq!(&file.data[..], b"Hello World!!!");
    }

    #[test]
    fn test_vfs_hierarchy_and_path_lookup() {
        let vfs = VfsRoot::new();
        vfs.populate_default_hierarchy();

        let root = vfs.root.read().unwrap();
        let entries = root.list_entries();
        assert!(entries.contains(&"etc/".to_string()));
        assert!(entries.contains(&"dev/".to_string()));

        let etc_dir = root.get_dir("etc").expect("missing /etc");
        let etc = etc_dir.read().unwrap();
        let os_rel_file = etc.get_file("os-release").expect("missing /etc/os-release");

        let file = os_rel_file.read().unwrap();
        let mut content = vec![0u8; file.size()];
        file.read(0, &mut content).unwrap();
        let text = String::from_utf8(content).unwrap();
        assert!(text.contains("NAME=\"VyronOS\""));
    }
}
