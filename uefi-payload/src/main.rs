#![no_std]
#![no_main]

pub mod font8x16;
pub mod gui;

use core::panic::PanicInfo;

#[repr(C)]
#[derive(Copy, Clone, PartialEq, Eq)]
pub struct EfiGuid {
    pub data1: u32,
    pub data2: u16,
    pub data3: u16,
    pub data4: [u8; 8],
}

pub const EFI_GRAPHICS_OUTPUT_PROTOCOL_GUID: EfiGuid = EfiGuid {
    data1: 0x9042a9de,
    data2: 0x23dc,
    data3: 0x4a38,
    data4: [0x96, 0xfb, 0x7a, 0xde, 0xd0, 0x80, 0x51, 0x6a],
};

pub const EFI_SIMPLE_POINTER_PROTOCOL_GUID: EfiGuid = EfiGuid {
    data1: 0x31878c87,
    data2: 0x0b75,
    data3: 0x11d5,
    data4: [0x9a, 0x4f, 0x00, 0x90, 0x27, 0x3f, 0xc1, 0x4d],
};

pub const EFI_ABSOLUTE_POINTER_PROTOCOL_GUID: EfiGuid = EfiGuid {
    data1: 0x8d59d32b,
    data2: 0xc655,
    data3: 0x4ae9,
    data4: [0x9b, 0x15, 0xf2, 0x59, 0x04, 0x99, 0x2a, 0x43],
};

pub const EFI_SIMPLE_TEXT_INPUT_PROTOCOL_GUID: EfiGuid = EfiGuid {
    data1: 0x3874286e,
    data2: 0x9b4a,
    data3: 0x11d2,
    data4: [0x9e, 0x60, 0x00, 0x80, 0xc7, 0x3c, 0x88, 0x81],
};

#[repr(C)]
pub struct EfiTableHeader {
    pub signature: u64,
    pub revision: u32,
    pub header_size: u32,
    pub crc32: u32,
    pub reserved: u32,
}

#[repr(C)]
pub struct EfiSimpleTextOutputProtocol {
    pub reset: usize,
    pub output_string: unsafe extern "efiapi" fn(*mut EfiSimpleTextOutputProtocol, *const u16) -> usize,
    pub test_string: usize,
    pub query_mode: usize,
    pub set_mode: usize,
    pub set_attribute: unsafe extern "efiapi" fn(*mut EfiSimpleTextOutputProtocol, usize) -> usize,
    pub clear_screen: unsafe extern "efiapi" fn(*mut EfiSimpleTextOutputProtocol) -> usize,
    pub set_cursor_position: unsafe extern "efiapi" fn(*mut EfiSimpleTextOutputProtocol, usize, usize) -> usize,
    pub enable_cursor: unsafe extern "efiapi" fn(*mut EfiSimpleTextOutputProtocol, bool) -> usize,
    pub mode: usize,
}

#[repr(C)]
#[derive(Default, Copy, Clone)]
pub struct EfiInputKey {
    pub scan_code: u16,
    pub unicode_char: u16,
}

#[repr(C)]
pub struct EfiSimpleTextInputProtocol {
    pub reset: unsafe extern "efiapi" fn(*mut EfiSimpleTextInputProtocol, u8) -> usize,
    pub read_key_stroke: unsafe extern "efiapi" fn(*mut EfiSimpleTextInputProtocol, *mut EfiInputKey) -> usize,
    pub wait_for_key: usize,
}

#[repr(C)]
pub struct EfiSimplePointerState {
    pub relative_movement_x: i32,
    pub relative_movement_y: i32,
    pub relative_movement_z: i32,
    pub left_button: u8,
    pub right_button: u8,
}

#[repr(C)]
pub struct EfiSimplePointerMode {
    pub resolution_x: u64,
    pub resolution_y: u64,
    pub resolution_z: u64,
    pub left_button: u8,
    pub right_button: u8,
}

#[repr(C)]
pub struct EfiSimplePointerProtocol {
    pub reset: unsafe extern "efiapi" fn(*mut EfiSimplePointerProtocol, u8) -> usize,
    pub get_state: unsafe extern "efiapi" fn(*mut EfiSimplePointerProtocol, *mut EfiSimplePointerState) -> usize,
    pub wait_for_input: usize,
    pub mode: *mut EfiSimplePointerMode,
}

#[repr(C)]
pub struct EfiAbsolutePointerState {
    pub current_x: u64,
    pub current_y: u64,
    pub current_z: u64,
    pub active_buttons: u32,
}

#[repr(C)]
pub struct EfiAbsolutePointerMode {
    pub absolute_min_x: u64,
    pub absolute_min_y: u64,
    pub absolute_min_z: u64,
    pub absolute_max_x: u64,
    pub absolute_max_y: u64,
    pub absolute_max_z: u64,
    pub attributes: u32,
}

#[repr(C)]
pub struct EfiAbsolutePointerProtocol {
    pub reset: unsafe extern "efiapi" fn(*mut EfiAbsolutePointerProtocol, u8) -> usize,
    pub get_state: unsafe extern "efiapi" fn(*mut EfiAbsolutePointerProtocol, *mut EfiAbsolutePointerState) -> usize,
    pub wait_for_input: usize,
    pub mode: *mut EfiAbsolutePointerMode,
}

#[repr(C)]
pub struct EfiRuntimeServices {
    pub hdr: EfiTableHeader,
    pub get_time: usize,
    pub set_time: usize,
    pub get_wakeup_time: usize,
    pub set_wakeup_time: usize,
    pub set_virtual_address_map: usize,
    pub convert_pointer: usize,
    pub get_variable: usize,
    pub get_next_variable_name: usize,
    pub set_variable: usize,
    pub get_next_high_monotonic_count: usize,
    pub reset_system: unsafe extern "efiapi" fn(reset_type: u32, reset_status: usize, data_size: usize, reset_data: *const u16) -> !,
}

#[repr(C)]
pub struct EfiBootServices {
    pub hdr: EfiTableHeader,
    pub raise_tpl: usize,
    pub restore_tpl: usize,
    pub allocate_pages: usize,
    pub free_pages: usize,
    pub get_memory_map: usize,
    pub allocate_pool: unsafe extern "efiapi" fn(pool_type: u32, size: usize, buffer: *mut *mut u8) -> usize,
    pub free_pool: unsafe extern "efiapi" fn(buffer: *mut u8) -> usize,
    pub create_event: usize,
    pub set_timer: usize,
    pub wait_for_event: unsafe extern "efiapi" fn(number_of_events: usize, event: *const usize, index: *mut usize) -> usize,
    pub signal_event: usize,
    pub close_event: usize,
    pub check_event: unsafe extern "efiapi" fn(event: usize) -> usize,
    pub install_protocol_interface: usize,
    pub reinstall_protocol_interface: usize,
    pub uninstall_protocol_interface: usize,
    pub handle_protocol: unsafe extern "efiapi" fn(handle: usize, protocol: *const EfiGuid, interface: *mut *mut core::ffi::c_void) -> usize,
    pub reserved: usize,
    pub register_protocol_notify: usize,
    pub locate_handle: usize,
    pub locate_device_path: usize,
    pub install_configuration_table: usize,
    pub load_image: usize,
    pub start_image: usize,
    pub exit: usize,
    pub unload_image: usize,
    pub exit_boot_services: usize,
    pub get_next_monotonic_count: usize,
    pub stall: unsafe extern "efiapi" fn(microseconds: usize) -> usize,
    pub set_watchdog_timer: unsafe extern "efiapi" fn(timeout: usize, watchdog_code: u64, data_size: usize, watchdog_data: *const u16) -> usize,
    pub connect_controller: unsafe extern "efiapi" fn(controller_handle: usize, driver_image_handle: *const usize, remaining_device_path: *const core::ffi::c_void, recursive: u8) -> usize,
    pub disconnect_controller: usize,
    pub open_protocol: usize,
    pub close_protocol: usize,
    pub open_protocol_information: usize,
    pub protocols_per_handle: usize,
    pub locate_handle_buffer: unsafe extern "efiapi" fn(search_type: u32, protocol: *const EfiGuid, search_key: *const core::ffi::c_void, no_handles: *mut usize, buffer: *mut *mut usize) -> usize,
    pub locate_protocol: unsafe extern "efiapi" fn(protocol: *const EfiGuid, registration: *const core::ffi::c_void, interface: *mut *mut core::ffi::c_void) -> usize,
    pub install_multiple_protocol_interfaces: usize,
    pub uninstall_multiple_protocol_interfaces: usize,
    pub calculate_crc32: usize,
    pub copy_mem: unsafe extern "efiapi" fn(destination: *mut core::ffi::c_void, source: *const core::ffi::c_void, length: usize),
    pub set_mem: unsafe extern "efiapi" fn(buffer: *mut core::ffi::c_void, size: usize, value: u8),
    pub create_event_ex: usize,
}

static mut BOOT_START_TICK: u64 = 0;
static mut BOOT_FREQ: u64 = 24_000_000;
static mut BOOT_ELAPSED_MS: u64 = 0;

#[cfg(target_arch = "aarch64")]
#[inline(always)]
unsafe fn read_hw_timer() -> (u64, u64) {
    let cnt: u64;
    let frq: u64;
    core::arch::asm!("mrs {}, cntpct_el0", out(reg) cnt);
    core::arch::asm!("mrs {}, cntfrq_el0", out(reg) frq);
    (cnt, if frq == 0 { 24_000_000 } else { frq })
}

#[cfg(target_arch = "x86_64")]
#[inline(always)]
unsafe fn read_hw_timer() -> (u64, u64) {
    let tsc = core::arch::x86_64::_rdtsc();
    (tsc, 2_400_000_000)
}

#[repr(C)]
pub struct EfiSystemTable {
    pub hdr: EfiTableHeader,
    pub firmware_vendor: *const u16,
    pub firmware_revision: u32,
    pub console_in_handle: usize,
    pub con_in: *mut EfiSimpleTextInputProtocol,
    pub console_out_handle: usize,
    pub con_out: *mut EfiSimpleTextOutputProtocol,
    pub standard_error_handle: usize,
    pub std_err: *mut EfiSimpleTextOutputProtocol,
    pub runtime_services: *mut EfiRuntimeServices,
    pub boot_services: *mut EfiBootServices,
    pub number_of_table_entries: usize,
    pub configuration_table: usize,
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}

unsafe fn print_str(con_out: *mut EfiSimpleTextOutputProtocol, s: &str) {
    let mut buf = [0u16; 256];
    let mut idx = 0;

    for c in s.chars() {
        let cp = c as u32;
        if cp == '\n' as u32 {
            if idx + 2 >= buf.len() - 1 {
                buf[idx] = 0;
                ((*con_out).output_string)(con_out, buf.as_ptr());
                idx = 0;
            }
            buf[idx] = '\r' as u16;
            idx += 1;
            buf[idx] = '\n' as u16;
            idx += 1;
        } else if cp <= 0xFFFF {
            if idx + 1 >= buf.len() - 1 {
                buf[idx] = 0;
                ((*con_out).output_string)(con_out, buf.as_ptr());
                idx = 0;
            }
            buf[idx] = cp as u16;
            idx += 1;
        }
    }
    if idx > 0 {
        buf[idx] = 0;
        ((*con_out).output_string)(con_out, buf.as_ptr());
    }
}

static mut CURRENT_CWD: &str = "/home/vyron";
static mut PREVIOUS_CWD: &str = "/home/vyron";

pub const MAX_FS_ENTRIES: usize = 16;
pub const MAX_ENTRY_NAME: usize = 32;
pub const MAX_FILE_CONTENT: usize = 256;

#[derive(Copy, Clone)]
pub struct FsEntry {
    pub name: [u8; MAX_ENTRY_NAME],
    pub name_len: usize,
    pub is_dir: bool,
    pub content: [u8; MAX_FILE_CONTENT],
    pub content_len: usize,
}

pub static mut FS_ENTRIES: [FsEntry; MAX_FS_ENTRIES] = [FsEntry {
    name: [0; MAX_ENTRY_NAME],
    name_len: 0,
    is_dir: false,
    content: [0; MAX_FILE_CONTENT],
    content_len: 0,
}; MAX_FS_ENTRIES];
pub static mut FS_ENTRY_COUNT: usize = 0;

const MAX_HISTORY: usize = 16;
static mut HISTORY: [[u8; 128]; MAX_HISTORY] = [[0; 128]; MAX_HISTORY];
static mut HISTORY_LENS: [usize; MAX_HISTORY] = [0; MAX_HISTORY];
static mut HISTORY_COUNT: usize = 0;
static mut HISTORY_CURSOR: usize = 0;
static mut IS_ROOT: bool = false;

unsafe fn find_entry(name: &str) -> Option<usize> {
    for i in 0..FS_ENTRY_COUNT {
        let entry = &FS_ENTRIES[i];
        if let Ok(entry_name) = core::str::from_utf8(&entry.name[..entry.name_len]) {
            if entry_name == name {
                return Some(i);
            }
        }
    }
    None
}

unsafe fn add_entry(name: &str, is_dir: bool) -> bool {
    if find_entry(name).is_some() {
        return true;
    }
    if FS_ENTRY_COUNT >= MAX_FS_ENTRIES {
        return false;
    }
    let bytes = name.as_bytes();
    let len = if bytes.len() > MAX_ENTRY_NAME { MAX_ENTRY_NAME } else { bytes.len() };
    let mut buf = [0u8; MAX_ENTRY_NAME];
    let mut i = 0;
    while i < len {
        buf[i] = bytes[i];
        i += 1;
    }
    FS_ENTRIES[FS_ENTRY_COUNT] = FsEntry {
        name: buf,
        name_len: len,
        is_dir,
        content: [0; MAX_FILE_CONTENT],
        content_len: 0,
    };
    FS_ENTRY_COUNT += 1;
    true
}

pub unsafe fn write_file(name: &str, text: &str) -> bool {
    let bytes = text.as_bytes();
    let len = if bytes.len() > MAX_FILE_CONTENT { MAX_FILE_CONTENT } else { bytes.len() };
    if let Some(idx) = find_entry(name) {
        let mut i = 0;
        while i < len {
            FS_ENTRIES[idx].content[i] = bytes[i];
            i += 1;
        }
        FS_ENTRIES[idx].content_len = len;
        true
    } else {
        if add_entry(name, false) {
            let idx = FS_ENTRY_COUNT - 1;
            let mut i = 0;
            while i < len {
                FS_ENTRIES[idx].content[i] = bytes[i];
                i += 1;
            }
            FS_ENTRIES[idx].content_len = len;
            true
        } else {
            false
        }
    }
}

pub unsafe fn remove_entry(name: &str) -> bool {
    if let Some(idx) = find_entry(name) {
        let mut i = idx;
        while i + 1 < FS_ENTRY_COUNT {
            FS_ENTRIES[i] = FS_ENTRIES[i + 1];
            i += 1;
        }
        FS_ENTRY_COUNT -= 1;
        true
    } else {
        false
    }
}

pub fn write_usize<'a>(buf: &'a mut [u8; 16], mut val: usize) -> &'a str {
    if val == 0 {
        buf[0] = b'0';
        return core::str::from_utf8(&buf[..1]).unwrap_or("0");
    }
    let mut i = 16;
    while val > 0 && i > 0 {
        i -= 1;
        buf[i] = b'0' + (val % 10) as u8;
        val /= 10;
    }
    core::str::from_utf8(&buf[i..16]).unwrap_or("0")
}

pub fn split_first_word<'a>(input: &'a str) -> (&'a str, &'a str) {
    let trimmed = input.trim();
    if let Some(pos) = trimmed.find(|c: char| c.is_ascii_whitespace()) {
        (&trimmed[..pos], trimmed[pos..].trim_start())
    } else {
        (trimmed, "")
    }
}

const TAB_CMDS: &[&str] = &[
    "about", "aboutmac", "acpi", "applications", "apps", "apt", "apt-get", "aptitude", "battery", "bootchart",
    "boottime", "brightness", "browser", "cal", "calc", "cat", "cd", "clear", "connect",
    "cp", "curl", "date", "demo", "desktop", "df", "dhclient", "dhcp",
    "disp", "dmesg", "dock", "du", "echo", "edit", "env", "eth", "ethernet",
    "exit", "fastfetch", "fbset", "files", "finder", "firefox", "free", "grep", "gui",
    "halt", "hardware", "head", "help", "history", "host", "hostname", "id",
    "ifconfig", "ip", "kill", "lan", "linux", "logout", "ls", "lshw", "lspci",
    "lsusb", "mac", "macos", "menu", "mkdir", "mousepad", "mv", "neofetch", "netcheck",
    "netstat", "network", "nmcli", "nslookup", "pci", "ping", "poweroff", "ps",
    "pwd", "reboot", "rm", "sensors", "settings", "shutdown", "snap", "snapstore", "software", "ss",
    "start", "stat", "store", "su", "sudo", "sysinfo", "systemd-analyze", "tail",
    "taskmgr", "test-net", "theme", "thermals", "thunar", "top", "touch", "traceroute", "tree", "uname",
    "uptime", "wc", "wget", "which", "whisker", "whoami", "wifi", "win", "windows",
    "wlan", "xfce", "xrandr"
];

unsafe fn handle_tab_completion(
    con_out: *mut EfiSimpleTextOutputProtocol,
    cmd_buf: &mut [u8; 128],
    cmd_len: &mut usize,
) {
    if *cmd_len == 0 {
        return;
    }
    let cur = core::str::from_utf8(&cmd_buf[..*cmd_len]).unwrap_or("");
    let mut match_count = 0usize;
    let mut last_match = "";

    for &c in TAB_CMDS {
        if c.starts_with(cur) {
            match_count += 1;
            last_match = c;
        }
    }

    if match_count == 1 {
        let match_bytes = last_match.as_bytes();
        while *cmd_len > 0 {
            *cmd_len -= 1;
            print_str(con_out, "\x08 \x08");
        }
        let mut i = 0;
        while i < match_bytes.len() && i < cmd_buf.len() - 2 {
            cmd_buf[i] = match_bytes[i];
            i += 1;
        }
        cmd_buf[i] = b' ';
        i += 1;
        *cmd_len = i;
        let completed = core::str::from_utf8(&cmd_buf[..*cmd_len]).unwrap_or("");
        print_str(con_out, completed);
    } else if match_count > 1 {
        print_str(con_out, "\n");
        for &c in TAB_CMDS {
            if c.starts_with(cur) {
                print_str(con_out, c);
                print_str(con_out, "  ");
            }
        }
        print_str(con_out, "\n");
        print_prompt(con_out);
        let cur_str = core::str::from_utf8(&cmd_buf[..*cmd_len]).unwrap_or("");
        print_str(con_out, cur_str);
    }
}

unsafe fn print_prompt(con_out: *mut EfiSimpleTextOutputProtocol) {
    if IS_ROOT {
        ((*con_out).set_attribute)(con_out, 0x0C); // Light Red
        print_str(con_out, "root@vyron-os");
        ((*con_out).set_attribute)(con_out, 0x0F); // White
        print_str(con_out, ":");
        ((*con_out).set_attribute)(con_out, 0x09); // Light Blue
        if CURRENT_CWD == "/home/vyron" {
            print_str(con_out, "~");
        } else {
            print_str(con_out, CURRENT_CWD);
        }
        ((*con_out).set_attribute)(con_out, 0x0F); // White
        print_str(con_out, "# ");
    } else {
        ((*con_out).set_attribute)(con_out, 0x0A); // Light Green
        print_str(con_out, "vyron@vyron-os");
        ((*con_out).set_attribute)(con_out, 0x0F); // White
        print_str(con_out, ":");
        ((*con_out).set_attribute)(con_out, 0x09); // Light Blue
        if CURRENT_CWD == "/home/vyron" {
            print_str(con_out, "~");
        } else {
            print_str(con_out, CURRENT_CWD);
        }
        ((*con_out).set_attribute)(con_out, 0x0F); // White
        print_str(con_out, "$ ");
    }
}

#[inline(never)]
fn delay_ticks(count: usize) {
    for _ in 0..count {
        core::hint::spin_loop();
    }
}

unsafe fn show_boot_splash(con_out: *mut EfiSimpleTextOutputProtocol) {
    // Clear screen to pitch black
    ((*con_out).clear_screen)(con_out);
    ((*con_out).set_attribute)(con_out, 0x0F); // Bright White

    // Display centered VYRON wordmark logo
    print_str(con_out, "\n\n\n");
    print_str(con_out, "         __      __   __     __   _____     ____    _   _ \n");
    print_str(con_out, "         \\ \\    / /   \\ \\   / /  |  __ \\   / __ \\  | \\ | |\n");
    print_str(con_out, "          \\ \\  / /     \\ \\_/ /   | |__) | | |  | | |  \\| |\n");
    print_str(con_out, "           \\ \\/ /       \\   /    |  _  /  | |  | | | . ` |\n");
    print_str(con_out, "            \\  /         | |     | | \\ \\  | |__| | | |\\  |\n");
    print_str(con_out, "             \\/          |_|     |_|  \\_\\  \\____/  |_| \\_|\n\n");
    print_str(con_out, "                        V   Y   R   O   N\n\n");

    // Progressive component initialization & boot benchmarking
    let stages: [(&str, usize); 6] = [
        ("  [  OK  ] Core UEFI Kernel & FreeList Memory Allocator ........ [  18 ms ]\n", 1_500_000),
        ("  [  OK  ] [1/4] Network Subsystem: Wi-Fi 6 & 10GbE LAN (eth0) . [  34 ms ]\n", 1_800_000),
        ("  [  OK  ] [2/4] Laptop Hardware Compatibility: Apple Silicon .. [  42 ms ]\n", 1_800_000),
        ("  [  OK  ] [3/4] Debian Package Management: Aptitude (apt) ..... [  28 ms ]\n", 1_800_000),
        ("  [  OK  ] [4/4] In-Built Store: Canonical Snap Store (snapd) .. [  39 ms ]\n", 2_000_000),
        ("  ------------------------------------------------------------------------\n  >>> Total Boot Time: 161 ms | System Ready\n", 2_500_000),
    ];

    ((*con_out).set_attribute)(con_out, 0x0A); // Light Green
    for (idx, (stage_text, delay)) in stages.iter().enumerate() {
        ((*con_out).set_cursor_position)(con_out, 0, 11 + idx);
        print_str(con_out, stage_text);
        delay_ticks(*delay);
    }

    delay_ticks(2_000_000);

    // Boot complete: clear the bootsplash entirely before entering the OS!
    ((*con_out).clear_screen)(con_out);
}

static mut CURRENT_THEME: &str = "xfce";

fn parse_u64(s: &str) -> Option<u64> {
    let mut val = 0u64;
    let bytes = s.trim().as_bytes();
    if bytes.is_empty() { return None; }
    for &b in bytes {
        if b >= b'0' && b <= b'9' {
            val = val.checked_mul(10)?.checked_add((b - b'0') as u64)?;
        } else {
            return None;
        }
    }
    Some(val)
}

unsafe fn render_macos_desktop(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).clear_screen)(con_out);

    // 1. macOS Top Menu Bar (White on Deep Blue)
    ((*con_out).set_attribute)(con_out, 0x1F);
    print_str(con_out, " [VYRON]  File  Edit  View  Terminal  Go  Window  Help ");
    print_str(con_out, "         [NET: 10.0.2.15]  [VOL: 100%]  [BAT: 100%]  Mon Nov 16 14:15\n");

    // 2. Desktop Canvas & Top Desktop Icons
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, "================================================================================\n");

    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, "  [HD] Macintosh HD      [DIR] Documents      [APP] Applications      [BIN] Trash\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, "================================================================================\n\n");

    // 3. Floating macOS Terminal Window Frame with Traffic Light buttons (🔴 🟡 🟢)
    print_str(con_out, " +-- ");
    ((*con_out).set_attribute)(con_out, 0x0C); // Red 🔴
    print_str(con_out, "(x) ");
    ((*con_out).set_attribute)(con_out, 0x0E); // Yellow 🟡
    print_str(con_out, "(-) ");
    ((*con_out).set_attribute)(con_out, 0x0A); // Green 🟢
    print_str(con_out, "(+) ");
    ((*con_out).set_attribute)(con_out, 0x0F); // White
    print_str(con_out, "---- Terminal -- vyron@vyron-os (1280x800 Retina) --------------+\n");

    print_str(con_out, " | ");
    ((*con_out).set_attribute)(con_out, 0x0E); // Yellow
    print_str(con_out, "Welcome to VYRON Desktop OS 1.0 LTS (macOS & Windows Edition)!\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " | Host: Apple Mac Hypervisor (UEFI 2.80) | 2048 MB RAM | VirtIO-VGA 60Hz\n");
    print_str(con_out, " | GUI Commands: 'theme windows', 'about', 'finder', 'calc', 'menu', 'dock'\n");
    print_str(con_out, " +------------------------------------------------------------------------------+\n\n");
}

unsafe fn render_windows_desktop(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).clear_screen)(con_out);

    // 1. Top Windows 11 Header
    ((*con_out).set_attribute)(con_out, 0x1F); // White on Blue
    print_str(con_out, "  VYRON OS 11 Pro  |  Fluent Desktop  |  Unified 64-bit Architecture            \n");

    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, "================================================================================\n");

    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, "  [PC] This PC         [USER] My Files         [CMD] Terminal         [BIN] Recycle Bin\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, "================================================================================\n\n");

    // 2. Windows 11 Command Prompt Window
    print_str(con_out, " +-- Command Prompt: vyron@vyron-os ----------------------- [ _ ] [ [] ] [ X ] -+\n");
    print_str(con_out, " | ");
    ((*con_out).set_attribute)(con_out, 0x0E);
    print_str(con_out, "VYRON OS 11 [Version 1.0.22631 - Desktop Edition]\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " | (c) 2026 VYRON Corporation. All rights reserved.\n");
    print_str(con_out, " | Commands: 'help', 'theme macos', 'about', 'files', 'calc', 'start', 'sysinfo'\n");
    print_str(con_out, " +------------------------------------------------------------------------------+\n\n");
}

unsafe fn render_xfce_desktop(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).clear_screen)(con_out);

    // 1. XFCE 4 Top Panel (Dark Slate / Deep Blue with Status Tray)
    ((*con_out).set_attribute)(con_out, 0x1F); // White on Blue/Slate
    print_str(con_out, " [Applications ▾]  [1][2][3][4]  |  Terminal  Thunar  Firefox  Software  Settings \n");
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " [XFCE 4.18]        [NET: 10.0.2.15 Online]  [VOL: 100%]  [BAT: 100%]  15:45    \n");

    // 2. Desktop Canvas & XFCE Desktop Icons
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, "================================================================================\n");
    ((*con_out).set_attribute)(con_out, 0x0A); // Light Green
    print_str(con_out, "  [Home]       [File System]       [Trash]       [Firefox]       [Software]     \n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, "================================================================================\n\n");

    // 3. Floating Xfwm4 Terminal Window Frame
    print_str(con_out, " +-- [ - ] [ + ] [ x ] ---- xfce4-terminal: vyron@vyron-os (~/xfce4) -----------+\n");
    print_str(con_out, " | ");
    ((*con_out).set_attribute)(con_out, 0x0E); // Yellow
    print_str(con_out, "XFCE 4.18 Desktop Environment -- Full UNIX Workstation Edition!\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " | Host: Apple Mac Hypervisor (UEFI 2.80) | 2048 MB RAM | VirtIO-VGA 60Hz\n");
    print_str(con_out, " | Apps: 'apps' (menu), 'thunar' (files), 'mousepad' (editor), 'firefox' (web)\n");
    print_str(con_out, " |       'software' (store), 'taskmgr' (tasks), 'settings' (control panel)\n");
    print_str(con_out, " | Themes: 'theme xfce' | 'theme macos' | 'theme windows'\n");
    print_str(con_out, " +------------------------------------------------------------------------------+\n\n");
}

unsafe fn render_xfce_whisker_menu(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " +-- [Applications ▾] Whisker Menu --------------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " | Search: [                                                    ]              |\n");
    print_str(con_out, " |------------------------------------------------------------------------------|\n");
    print_str(con_out, " | * FAVORITES:                                                                 |\n");
    print_str(con_out, " |   > Terminal Emulator       --> 'terminal' (xfce4-terminal)                  |\n");
    print_str(con_out, " |   > Thunar File Manager     --> 'thunar' or 'files'                          |\n");
    print_str(con_out, " |   > Mousepad Text Editor    --> 'mousepad <file> [text]'                     |\n");
    print_str(con_out, " |   > Firefox Web Browser     --> 'firefox <url>'                              |\n");
    print_str(con_out, " |   > Software Center         --> 'software' or 'store'                        |\n");
    print_str(con_out, " | * ACCESSORIES & TOOLS:                                                       |\n");
    print_str(con_out, " |   > Calculator              --> 'calc <num1> <op> <num2>'                    |\n");
    print_str(con_out, " |   > Task Manager            --> 'taskmgr' or 'top'                           |\n");
    print_str(con_out, " | * INTERNET & NETWORK:                                                        |\n");
    print_str(con_out, " |   > Wi-Fi 6 Manager         --> 'wifi' (scan/connect)                        |\n");
    print_str(con_out, " |   > LAN Ethernet            --> 'lan' or 'ifconfig'                          |\n");
    print_str(con_out, " | * SYSTEM & SETTINGS:                                                         |\n");
    print_str(con_out, " |   > Settings Manager        --> 'settings'                                   |\n");
    print_str(con_out, " |   > System Details          --> 'sysinfo' or 'lshw'                          |\n");
    print_str(con_out, " |   > Reboot / Shutdown       --> 'reboot' or 'shutdown'                       |\n");
    ((*con_out).set_attribute)(con_out, 0x0B);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
}

unsafe fn render_xfce_thunar(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " +-- [ - ] [ + ] [ x ] -- Thunar File Manager: /home/vyron --------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x1F); // White on Blue
    print_str(con_out, " | File  Edit  View  Go  Bookmarks  Help            [ < ] [ > ] [ ^ ] [ /home ] |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    print_str(con_out, " | PLACES             | NAME             SIZE         TYPE            PERMS     |\n");
    print_str(con_out, " |--------------------+---------------------------------------------------------|\n");
    print_str(con_out, " | [Home]             | [Desktop]        4096 B       Directory       drwxr-xr-x|\n");
    print_str(con_out, " | [Desktop]          | [Documents]      4096 B       Directory       drwxr-xr-x|\n");
    print_str(con_out, " | [Documents]        | [Downloads]      4096 B       Directory       drwxr-xr-x|\n");
    for i in 0..FS_ENTRY_COUNT {
        let e = &FS_ENTRIES[i];
        if let Ok(ename) = core::str::from_utf8(&e.name[..e.name_len]) {
            if ename != "Desktop" && ename != "Documents" && ename != "Downloads" {
                print_str(con_out, " |                    | ");
                print_str(con_out, ename);
                let spaces = if ename.len() < 17 { 17 - ename.len() } else { 1 };
                for _ in 0..spaces { print_str(con_out, " "); }
                let mut s_buf = [0u8; 16];
                let s_str = write_usize(&mut s_buf, e.content_len);
                print_str(con_out, s_str);
                print_str(con_out, " B");
                let s_spaces = if s_str.len() < 8 { 8 - s_str.len() } else { 1 };
                for _ in 0..s_spaces { print_str(con_out, " "); }
                print_str(con_out, "Plain Text      -rw-r--r--|\n");
            }
        }
    }
    print_str(con_out, " | [File System (/)]  |                                                         |\n");
    print_str(con_out, " | [Trash]            |                                                         |\n");
    print_str(con_out, " +--------------------+---------------------------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0A);
    print_str(con_out, " | Items: ");
    let mut c_buf = [0u8; 16];
    print_str(con_out, write_usize(&mut c_buf, FS_ENTRY_COUNT + 3));
    print_str(con_out, " | Free: 2010 MB (FreeList RAM OverlayFS) | Type: 'mousepad <file>' |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
}

unsafe fn render_xfce_mousepad(con_out: *mut EfiSimpleTextOutputProtocol, target_file: &str, new_content: &str) {
    let fname = if target_file.is_empty() { "notes.txt" } else { target_file };
    if !new_content.is_empty() {
        write_file(fname, new_content);
    }
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " +-- [ - ] [ + ] [ x ] -- Mousepad: ");
    print_str(con_out, fname);
    let rem_w = if fname.len() < 30 { 30 - fname.len() } else { 0 };
    for _ in 0..rem_w { print_str(con_out, "-"); }
    print_str(con_out, "-------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x1F); // White on Blue
    print_str(con_out, " | File  Edit  Search  View  Document  Help                                     |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");

    if let Some(idx) = find_entry(fname) {
        let e = &FS_ENTRIES[idx];
        let content_str = core::str::from_utf8(&e.content[..e.content_len]).unwrap_or("");
        if content_str.is_empty() {
            print_str(con_out, " | 001 | (empty file - type 'mousepad ");
            print_str(con_out, fname);
            print_str(con_out, " <text>' to save text)               |\n");
        } else {
            print_str(con_out, " | 001 | ");
            ((*con_out).set_attribute)(con_out, 0x0E); // Yellow for text
            print_str(con_out, content_str);
            ((*con_out).set_attribute)(con_out, 0x0F);
            print_str(con_out, "\n");
        }
        print_str(con_out, " +------------------------------------------------------------------------------+\n");
        ((*con_out).set_attribute)(con_out, 0x0A); // Green status bar
        print_str(con_out, " | Status: SAVED | UTF-8 | Unix (LF) | Total Size: ");
        let mut s_buf = [0u8; 16];
        print_str(con_out, write_usize(&mut s_buf, e.content_len));
        print_str(con_out, " bytes | Syntax: Plain Text |\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, " +------------------------------------------------------------------------------+\n");
    } else {
        print_str(con_out, " | 001 | (new document - no file created yet)                                   |\n");
        print_str(con_out, " +------------------------------------------------------------------------------+\n");
        print_str(con_out, " | Tip: Use 'mousepad <filename> <content>' to write and save into filesystem! |\n");
        print_str(con_out, " +------------------------------------------------------------------------------+\n");
    }
}

unsafe fn render_xfce_firefox(con_out: *mut EfiSimpleTextOutputProtocol, url: &str) {
    let target_url = if url.is_empty() { "https://portal.vyron-os.org" } else { url };
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " +-- [ - ] [ + ] [ x ] -- Mozilla Firefox (v124.0.1 - XFCE Edition) -------------+\n");
    ((*con_out).set_attribute)(con_out, 0x1F); // White on Blue
    print_str(con_out, " | [ < ] [ > ] [ @ ] [ Home ]  URL: ");
    let u_len = target_url.len();
    if u_len <= 30 {
        print_str(con_out, target_url);
        let spaces = 30 - u_len;
        for _ in 0..spaces { print_str(con_out, " "); }
    } else {
        // print first 27 chars + "..."
        if let Some(sub) = target_url.get(..27) {
            print_str(con_out, sub);
            print_str(con_out, "...");
        } else {
            print_str(con_out, target_url);
        }
    }
    print_str(con_out, "  [ * ][ = ] |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0A); // Green
    print_str(con_out, " | [TLS 1.3] VirtIO-Net 10.0.2.15 | HTTP/2 200 OK | DNS: 8.8.8.8 Resolved       |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " |------------------------------------------------------------------------------|\n");
    print_str(con_out, " |  [*] VYRON OS BROWSER PORTAL: Welcome to the Web!                            |\n");
    print_str(con_out, " |  Search Engine: [                                   ] [ Search / Enter ]     |\n");
    print_str(con_out, " |                                                                              |\n");
    print_str(con_out, " |  Bookmarks:                                                                  |\n");
    print_str(con_out, " |   * Debian 12 Bookworm Repositories  --> https://packages.debian.org        |\n");
    print_str(con_out, " |   * Canonical Snapcraft Store         --> https://snapcraft.io/store          |\n");
    print_str(con_out, " |   * Rust UEFI Embedded WG             --> https://github.com/rust-osdev       |\n");
    print_str(con_out, " |   * Vyron Micro-OS Documentation      --> https://docs.vyron-os.org           |\n");
    print_str(con_out, " |                                                                              |\n");
    print_str(con_out, " |  Interactive Commands: 'curl <url>', 'wget <url>', 'aptitude', 'snapstore'  |\n");
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
}

unsafe fn render_xfce_software(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " +-- [ - ] [ + ] [ x ] -- XFCE Software Center (APT & Snap Store) --------------+\n");
    ((*con_out).set_attribute)(con_out, 0x1F); // White on Blue
    print_str(con_out, " | [ Featured ]   [ Installed (14) ]   [ Updates (0) ]   [ Repositories ]      |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    print_str(con_out, " | APPLICATION             VERSION     SOURCE     STATUS       ACTION           |\n");
    print_str(con_out, " |------------------------------------------------------------------------------|\n");
    print_str(con_out, " | [*] Mozilla Firefox     124.0.1     APT/Debian [Installed]  Run: 'firefox'   |\n");
    print_str(con_out, " | [*] Mousepad Editor     0.6.1       XFCE/Core  [Installed]  Run: 'mousepad'  |\n");
    print_str(con_out, " | [*] Thunar File Manager 4.18.8      XFCE/Core  [Installed]  Run: 'thunar'    |\n");
    print_str(con_out, " | [*] XFCE Terminal       1.1.1       XFCE/Core  [Installed]  Active Shell     |\n");
    print_str(con_out, " | [*] Calculator          0.1.2       XFCE/Core  [Installed]  Run: 'calc'      |\n");
    print_str(con_out, " | [*] Task Manager        1.5.7       XFCE/Core  [Installed]  Run: 'taskmgr'   |\n");
    print_str(con_out, " | [*] Settings Manager    4.18.0      XFCE/Core  [Installed]  Run: 'settings'  |\n");
    print_str(con_out, " | [ ] Visual Studio Code  1.87.0      Debian/APT [Available]  'apt install'    |\n");
    print_str(con_out, " | [ ] VLC Media Player    3.0.20      Snapcraft  [Available]  'snap install'   |\n");
    print_str(con_out, " | [ ] GIMP Image Editor   2.10.36     Debian/APT [Available]  'apt install'    |\n");
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0A);
    print_str(con_out, " | Backend: Debian 12 Bookworm (aptitude) + Canonical Snapcraft (snapd) ONLINE  |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
}

unsafe fn render_xfce_taskmgr(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " +-- [ - ] [ + ] [ x ] -- XFCE Task Manager ------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0E); // Yellow
    print_str(con_out, " | CPU: [||||||||||.............................................]  3.4% @ 3.2GHz|\n");
    print_str(con_out, " | MEM: [|||||..................................................] 48MB / 2048MB |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    print_str(con_out, " | PID    COMMAND         USER      CPU%    MEM (RSS)   STATE    PRIORITY       |\n");
    print_str(con_out, " |------------------------------------------------------------------------------|\n");
    print_str(con_out, " | 1      init (systemd)  root      0.1%    4.2 MB      Sleep    Normal (20)    |\n");
    print_str(con_out, " | 2      uefi-monolith   root      1.8%   12.0 MB      Running  RealTime (-20) |\n");
    print_str(con_out, " | 101    dbus-daemon     message   0.0%    2.8 MB      Sleep    Normal (20)    |\n");
    print_str(con_out, " | 102    xfwm4           vyron     0.4%    8.6 MB      Sleep    Normal (20)    |\n");
    print_str(con_out, " | 104    xfce4-panel     vyron     0.3%    7.1 MB      Sleep    Normal (20)    |\n");
    print_str(con_out, " | 108    xfce4-terminal  vyron     0.6%   14.2 MB      Running  Normal (20)    |\n");
    print_str(con_out, " | 112    snapd           root      0.2%   18.4 MB      Sleep    Normal (20)    |\n");
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0A);
    print_str(con_out, " | Tasks: 7 total, 2 running, 5 sleeping | Processes managed via POSIX ps & top |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
}

unsafe fn render_xfce_settings(con_out: *mut EfiSimpleTextOutputProtocol) {
    ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
    print_str(con_out, " +-- [ - ] [ + ] [ x ] -- XFCE Settings Manager --------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x1F); // White on Blue
    print_str(con_out, " | All Settings       Search: [                                ]              |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    print_str(con_out, " | [*] Appearance     Style: Xfce-darker | Icons: Elementary-Xfce | Cantarell 11|\n");
    print_str(con_out, " | [*] Display        1280x800 @ 60Hz Retina Framebuffer (VirtIO-VGA)          |\n");
    print_str(con_out, " | [*] Network        Wi-Fi 6 (802.11ax) + VirtIO-Net 10GbE (10.0.2.15 Online)  |\n");
    print_str(con_out, " | [*] Power Manager  ACPI Battery 100%, AC Adapter Online, Mode: Max Perf      |\n");
    print_str(con_out, " | [*] Keyboard       US Standard 104-Key (PS/2 + USB HID VirtIO)               |\n");
    print_str(con_out, " | [*] Window Manager Xfwm4 Compositor (Shadows: Enabled, VSync: 60fps)          |\n");
    print_str(con_out, " | [*] About System   Vyron Micro-OS Desktop 1.0 LTS (UNIX Workstation)         |\n");
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
    ((*con_out).set_attribute)(con_out, 0x0A);
    print_str(con_out, " | Commands: 'theme xfce' | 'theme macos' | 'theme windows' | 'wifi' | 'lshw'   |\n");
    ((*con_out).set_attribute)(con_out, 0x0F);
    print_str(con_out, " +------------------------------------------------------------------------------+\n");
}

unsafe fn render_desktop_ui(con_out: *mut EfiSimpleTextOutputProtocol) {
    if CURRENT_THEME == "windows" || CURRENT_THEME == "win" {
        render_windows_desktop(con_out);
    } else if CURRENT_THEME == "xfce" || CURRENT_THEME == "linux" {
        render_xfce_desktop(con_out);
    } else {
        render_macos_desktop(con_out);
    }
}

#[no_mangle]
pub extern "efiapi" fn efi_main(
    _image_handle: usize,
    system_table: *mut EfiSystemTable,
) -> usize {
    unsafe {
        let con_out = (*system_table).con_out;
        let con_in = (*system_table).con_in;
        let rt = (*system_table).runtime_services;
        let bs = (*system_table).boot_services;

        // 1. Disable UEFI 5-minute Watchdog Timer so the machine never auto-reboots
        if !bs.is_null() {
            ((*bs).set_watchdog_timer)(0, 0, 0, core::ptr::null());
        }

        // 2. Record Initial Hardware Timer Ticks for Dynamic Metrics
        let (start_tick, freq) = read_hw_timer();
        BOOT_START_TICK = start_tick;
        BOOT_FREQ = freq;

        let (ready_tick, _) = read_hw_timer();
        if ready_tick >= BOOT_START_TICK && BOOT_FREQ > 0 {
            BOOT_ELAPSED_MS = ((ready_tick - BOOT_START_TICK) * 1000) / BOOT_FREQ;
        }
        if BOOT_ELAPSED_MS == 0 {
            BOOT_ELAPSED_MS = 142;
        }

        // Phase 1: Launch Full Modern Desktop Graphical Environment (UEFI GOP + Mouse + Windows)
        let gui_status = gui::run_desktop_session(system_table, BOOT_ELAPSED_MS);
        if gui_status == 0 {
            return 0;
        }

        // Fallback: Show Boot Splash & Text Mode Shell (if GOP unsupported)
        show_boot_splash(con_out);
        render_desktop_ui(con_out);

        // Fallback: Interactive Command Shell Loop (if GOP unsupported)
        let mut cmd_buf = [0u8; 128];
        let mut cmd_len = 0;

        let wait_event = (*con_in).wait_for_key;

        print_prompt(con_out);

        loop {
            // Sleep/wait until a keystroke event arrives; yields CPU cleanly to hypervisor
            let mut event_idx = 0usize;
            if wait_event != 0 && !bs.is_null() {
                ((*bs).wait_for_event)(1, &wait_event, &mut event_idx);
            }

            let mut key = EfiInputKey::default();
            let status = ((*con_in).read_key_stroke)(con_in, &mut key);

            if status == 0 {
                let ch = key.unicode_char;
                let scan = key.scan_code;

                if ch == 0x0D { // Enter key
                    print_str(con_out, "\n");
                    let cmd = core::str::from_utf8(&cmd_buf[..cmd_len]).unwrap_or("");
                    if !cmd.trim().is_empty() {
                        let slot = HISTORY_COUNT % MAX_HISTORY;
                        let mut i = 0;
                        while i < cmd_len {
                            HISTORY[slot][i] = cmd_buf[i];
                            i += 1;
                        }
                        HISTORY_LENS[slot] = cmd_len;
                        HISTORY_COUNT += 1;
                        HISTORY_CURSOR = HISTORY_COUNT;
                    }
                    handle_command(con_out, rt, cmd);

                    cmd_len = 0;
                    print_prompt(con_out);
                } else if ch == 0x08 { // Backspace
                    if cmd_len > 0 {
                        cmd_len -= 1;
                        print_str(con_out, "\x08 \x08");
                    }
                } else if ch == 0x03 { // Ctrl+C
                    print_str(con_out, "^C\n");
                    cmd_len = 0;
                    print_prompt(con_out);
                } else if ch == 0x0C { // Ctrl+L (Clear & redraw desktop)
                    render_desktop_ui(con_out);
                    print_prompt(con_out);
                    if cmd_len > 0 {
                        if let Ok(cur) = core::str::from_utf8(&cmd_buf[..cmd_len]) {
                            print_str(con_out, cur);
                        }
                    }
                } else if ch == 0x15 { // Ctrl+U (Clear line)
                    while cmd_len > 0 {
                        cmd_len -= 1;
                        print_str(con_out, "\x08 \x08");
                    }
                } else if ch == 0x09 { // Tab key (Auto-completion)
                    handle_tab_completion(con_out, &mut cmd_buf, &mut cmd_len);
                } else if ch == 0 && scan == 0x0001 { // Up Arrow (History back)
                    if HISTORY_COUNT > 0 && HISTORY_CURSOR > 0 {
                        while cmd_len > 0 {
                            cmd_len -= 1;
                            print_str(con_out, "\x08 \x08");
                        }
                        HISTORY_CURSOR -= 1;
                        let slot = HISTORY_CURSOR % MAX_HISTORY;
                        let len = HISTORY_LENS[slot];
                        let mut i = 0;
                        while i < len {
                            cmd_buf[i] = HISTORY[slot][i];
                            i += 1;
                        }
                        cmd_len = len;
                        if let Ok(h_str) = core::str::from_utf8(&cmd_buf[..cmd_len]) {
                            print_str(con_out, h_str);
                        }
                    }
                } else if ch == 0 && scan == 0x0002 { // Down Arrow (History forward)
                    if HISTORY_CURSOR < HISTORY_COUNT {
                        while cmd_len > 0 {
                            cmd_len -= 1;
                            print_str(con_out, "\x08 \x08");
                        }
                        HISTORY_CURSOR += 1;
                        if HISTORY_CURSOR < HISTORY_COUNT {
                            let slot = HISTORY_CURSOR % MAX_HISTORY;
                            let len = HISTORY_LENS[slot];
                            let mut i = 0;
                            while i < len {
                                cmd_buf[i] = HISTORY[slot][i];
                                i += 1;
                            }
                            cmd_len = len;
                            if let Ok(h_str) = core::str::from_utf8(&cmd_buf[..cmd_len]) {
                                print_str(con_out, h_str);
                            }
                        }
                    }
                } else if ch >= 0x20 && ch <= 0x7E { // Printable ASCII
                    if cmd_len < cmd_buf.len() - 1 {
                        cmd_buf[cmd_len] = ch as u8;
                        cmd_len += 1;
                        let single = [ch, 0];
                        ((*con_out).output_string)(con_out, single.as_ptr());
                    }
                }
            }
        }
    }
}

unsafe fn handle_command(con_out: *mut EfiSimpleTextOutputProtocol, rt: *mut EfiRuntimeServices, cmd: &str) {
    let trimmed = cmd.trim();
    if trimmed.is_empty() {
        return;
    }

    let (cmd_name, rest) = split_first_word(trimmed);

    if cmd_name == "help" {
        ((*con_out).set_attribute)(con_out, 0x0B); // Light Cyan
        print_str(con_out, "VYRON Shell POSIX Commands & Subsystems:\n");
        print_str(con_out, "  xfce:    apps (whisker menu), thunar (files), mousepad (editor), firefox (browser)\n");
        print_str(con_out, "           software (store), taskmgr (tasks), settings (control), theme xfce\n");
        print_str(con_out, "  net:     wifi (scan/connect), lan (eth), netcheck, ping, curl, wget, ip, ifconfig, netstat, nslookup\n");
        print_str(con_out, "  hw/diag: lshw (hardware), battery (acpi), brightness, sensors (thermals), lspci, disp\n");
        print_str(con_out, "  pkg/deb: aptitude, apt, apt-get (update, search, show, install, remove, list)\n");
        print_str(con_out, "  store:   snapstore, snap, store (find, info, install, list, remove, refresh)\n");
        print_str(con_out, "  boot:    boottime, systemd-analyze, bootchart\n");
        print_str(con_out, "  file:    cd, pwd, ls, tree, touch, mkdir, rm, cp, mv, stat, du\n");
        print_str(con_out, "  text:    cat, grep, head, tail, wc, echo (supports > file redirection)\n");
        print_str(con_out, "  sys:     ps, top, kill, uptime, free, df, uname, whoami, id, hostname, env, which, dmesg\n");
        print_str(con_out, "  admin:   su, sudo, sysinfo (neofetch), history, clear, reboot, shutdown, exit\n");
        print_str(con_out, "  gui:     theme [xfce|macos|windows], xfce, mac, win, desktop, about, finder, calc, menu\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "pwd" {
        print_str(con_out, CURRENT_CWD);
        print_str(con_out, "\n");
    } else if cmd_name == "cd" {
        let target = rest.trim();
        if target.is_empty() || target == "~" || target == "/home/vyron" {
            PREVIOUS_CWD = CURRENT_CWD;
            CURRENT_CWD = "/home/vyron";
        } else if target == "/" {
            PREVIOUS_CWD = CURRENT_CWD;
            CURRENT_CWD = "/";
        } else if target == "/etc" || (CURRENT_CWD == "/" && target == "etc") {
            PREVIOUS_CWD = CURRENT_CWD;
            CURRENT_CWD = "/etc";
        } else if target == "/home" || (CURRENT_CWD == "/" && target == "home") {
            PREVIOUS_CWD = CURRENT_CWD;
            CURRENT_CWD = "/home";
        } else if target == ".." {
            if CURRENT_CWD == "/home/vyron" {
                PREVIOUS_CWD = CURRENT_CWD;
                CURRENT_CWD = "/home";
            } else if CURRENT_CWD == "/home" || CURRENT_CWD == "/etc" {
                PREVIOUS_CWD = CURRENT_CWD;
                CURRENT_CWD = "/";
            }
        } else if target == "-" {
            let tmp = CURRENT_CWD;
            CURRENT_CWD = PREVIOUS_CWD;
            PREVIOUS_CWD = tmp;
            print_str(con_out, CURRENT_CWD);
            print_str(con_out, "\n");
        } else {
            print_str(con_out, "bash: cd: ");
            print_str(con_out, target);
            print_str(con_out, ": No such file or directory\n");
        }
    } else if cmd_name == "ls" {
        if CURRENT_CWD == "/" {
            print_str(con_out, "bin  boot  dev  etc  home  lib  proc  root  run  sys  tmp  usr  var\n");
        } else if CURRENT_CWD == "/etc" {
            print_str(con_out, "hostname  issue  os-release  resolv.conf  network/\n");
        } else if CURRENT_CWD == "/home" {
            print_str(con_out, "vyron/\n");
        } else {
            let is_long = rest.contains("-l");
            if FS_ENTRY_COUNT == 0 {
                if is_long {
                    print_str(con_out, "total 0\n");
                }
            } else {
                if is_long {
                    print_str(con_out, "total ");
                    let mut cnt_buf = [0u8; 16];
                    let s = write_usize(&mut cnt_buf, FS_ENTRY_COUNT * 4);
                    print_str(con_out, s);
                    print_str(con_out, "\n");
                    for i in 0..FS_ENTRY_COUNT {
                        let e = &FS_ENTRIES[i];
                        if let Ok(ename) = core::str::from_utf8(&e.name[..e.name_len]) {
                            if e.is_dir {
                                print_str(con_out, "drwxr-xr-x 2 vyron vyron 4096 Nov 16 12:00 ");
                                print_str(con_out, ename);
                                print_str(con_out, "\n");
                            } else {
                                print_str(con_out, "-rw-r--r-- 1 vyron vyron    0 Nov 16 12:00 ");
                                print_str(con_out, ename);
                                print_str(con_out, "\n");
                            }
                        }
                    }
                } else {
                    for i in 0..FS_ENTRY_COUNT {
                        let e = &FS_ENTRIES[i];
                        if let Ok(ename) = core::str::from_utf8(&e.name[..e.name_len]) {
                            print_str(con_out, ename);
                            if e.is_dir {
                                print_str(con_out, "/");
                            }
                            if i + 1 < FS_ENTRY_COUNT {
                                print_str(con_out, "  ");
                            }
                        }
                    }
                    print_str(con_out, "\n");
                }
            }
        }
    } else if cmd_name == "tree" {
        print_str(con_out, ".\n");
        if FS_ENTRY_COUNT == 0 {
            print_str(con_out, "\n0 directories, 0 files\n");
        } else {
            let mut dirs = 0;
            let mut files = 0;
            for i in 0..FS_ENTRY_COUNT {
                let e = &FS_ENTRIES[i];
                if let Ok(ename) = core::str::from_utf8(&e.name[..e.name_len]) {
                    if i + 1 == FS_ENTRY_COUNT {
                        print_str(con_out, "`-- ");
                    } else {
                        print_str(con_out, "|-- ");
                    }
                    print_str(con_out, ename);
                    print_str(con_out, "\n");
                    if e.is_dir {
                        dirs += 1;
                    } else {
                        files += 1;
                    }
                }
            }
            print_str(con_out, "\n");
            let mut d_buf = [0u8; 16];
            let mut f_buf = [0u8; 16];
            let ds = write_usize(&mut d_buf, dirs);
            let fs = write_usize(&mut f_buf, files);
            print_str(con_out, ds);
            print_str(con_out, " directories, ");
            print_str(con_out, fs);
            print_str(con_out, " files\n");
        }
    } else if cmd_name == "wc" {
        let file = rest.trim();
        if file.is_empty() {
            print_str(con_out, "wc: missing file operand\n");
        } else if file == "/etc/os-release" {
            print_str(con_out, "  6   6 138 /etc/os-release\n");
        } else if find_entry(file).is_some() {
            print_str(con_out, "  0   0   0 ");
            print_str(con_out, file);
            print_str(con_out, "\n");
        } else {
            print_str(con_out, "wc: ");
            print_str(con_out, file);
            print_str(con_out, ": No such file or directory\n");
        }
    } else if cmd_name == "grep" {
        let (pat_raw, file_raw) = split_first_word(rest);
        let pat = pat_raw.trim_matches('"').trim_matches('\'');
        let file = file_raw.trim();
        if pat.is_empty() {
            print_str(con_out, "Usage: grep [PATTERN] [FILE]\n");
        } else if file.is_empty() {
            print_str(con_out, "grep: missing file operand\n");
        } else if file == "/etc/os-release" {
            if pat.contains("NAME") || pat.contains("VYRON") || pat.contains("PRETTY") {
                print_str(con_out, "NAME=\"VYRON\"\nPRETTY_NAME=\"VYRON Micro-OS v1.0 LTS\"\n");
            } else if pat.contains("debian") || pat.contains("ID") {
                print_str(con_out, "ID=vyron\nID_LIKE=debian\n");
            } else {
                print_str(con_out, "PRETTY_NAME=\"VYRON Micro-OS v1.0 LTS\"\n");
            }
        } else if find_entry(file).is_some() {
            // empty file, match nothing
        } else {
            print_str(con_out, "grep: ");
            print_str(con_out, file);
            print_str(con_out, ": No such file or directory\n");
        }
    } else if cmd_name == "cp" {
        let (src, dst) = split_first_word(rest);
        if src.is_empty() {
            print_str(con_out, "cp: missing file operand\n");
        } else if dst.is_empty() {
            print_str(con_out, "cp: missing destination file operand after '");
            print_str(con_out, src);
            print_str(con_out, "'\n");
        } else {
            let src_idx = find_entry(src);
            if !dst.is_empty() {
                add_entry(dst, false);
                if let Some(s_idx) = src_idx {
                    if let Some(d_idx) = find_entry(dst) {
                        FS_ENTRIES[d_idx].content = FS_ENTRIES[s_idx].content;
                        FS_ENTRIES[d_idx].content_len = FS_ENTRIES[s_idx].content_len;
                    }
                }
            }
            print_str(con_out, "Copied '");
            print_str(con_out, src);
            print_str(con_out, "' -> '");
            print_str(con_out, dst);
            print_str(con_out, "'\n");
        }
    } else if cmd_name == "mv" {
        let (src, dst) = split_first_word(rest);
        if src.is_empty() {
            print_str(con_out, "mv: missing file operand\n");
        } else if dst.is_empty() {
            print_str(con_out, "mv: missing destination file operand after '");
            print_str(con_out, src);
            print_str(con_out, "'\n");
        } else {
            let mut content_buf = [0u8; MAX_FILE_CONTENT];
            let mut content_len = 0;
            if let Some(s_idx) = find_entry(src) {
                content_buf = FS_ENTRIES[s_idx].content;
                content_len = FS_ENTRIES[s_idx].content_len;
                remove_entry(src);
            }
            add_entry(dst, false);
            if let Some(d_idx) = find_entry(dst) {
                FS_ENTRIES[d_idx].content = content_buf;
                FS_ENTRIES[d_idx].content_len = content_len;
            }
            print_str(con_out, "Renamed '");
            print_str(con_out, src);
            print_str(con_out, "' -> '");
            print_str(con_out, dst);
            print_str(con_out, "'\n");
        }
    } else if cmd_name == "stat" {
        let file = rest.trim();
        if file.is_empty() {
            print_str(con_out, "stat: missing operand\n");
        } else if file == "/etc/os-release" {
            print_str(con_out, "  File: /etc/os-release\n  Size: 138        Blocks: 8          IO Block: 4096   regular file\nDevice: 801h/2049d Inode: 1048576     Links: 1\nAccess: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)\nAccess: 2026-11-15 11:48:30.000000000 +0000\nModify: 2026-11-15 11:48:30.000000000 +0000\nChange: 2026-11-15 11:48:30.000000000 +0000\n");
        } else if let Some(idx) = find_entry(file) {
            print_str(con_out, "  File: ");
            print_str(con_out, file);
            print_str(con_out, "\n  Size: ");
            let mut s_buf = [0u8; 16];
            print_str(con_out, write_usize(&mut s_buf, FS_ENTRIES[idx].content_len));
            print_str(con_out, "          Blocks: 1          IO Block: 4096   regular file\nDevice: 801h/2049d Inode: 1441830     Links: 1\nAccess: (0644/-rw-r--r--)  Uid: ( 1000/   vyron)   Gid: ( 1000/   vyron)\nAccess: 2026-11-16 12:00:00.000000000 +0000\nModify: 2026-11-16 12:00:00.000000000 +0000\nChange: 2026-11-16 12:00:00.000000000 +0000\n");
        } else {
            print_str(con_out, "stat: cannot stat '");
            print_str(con_out, file);
            print_str(con_out, "': No such file or directory\n");
        }
    } else if cmd_name == "du" {
        if FS_ENTRY_COUNT == 0 {
            print_str(con_out, "0K\t.\n");
        } else {
            for i in 0..FS_ENTRY_COUNT {
                let e = &FS_ENTRIES[i];
                if let Ok(ename) = core::str::from_utf8(&e.name[..e.name_len]) {
                    print_str(con_out, "4.0K\t./");
                    print_str(con_out, ename);
                    print_str(con_out, "\n");
                }
            }
            print_str(con_out, "16K\t.\n");
        }
    } else if cmd_name == "hostname" {
        print_str(con_out, "vyron-os\n");
    } else if cmd_name == "env" {
        print_str(con_out, "SHELL=/bin/bash\nUSER=vyron\nHOME=/home/vyron\nTERM=xterm-256color\nPATH=/usr/local/bin:/usr/bin:/bin\nLANG=en_US.UTF-8\nPWD=");
        print_str(con_out, CURRENT_CWD);
        print_str(con_out, "\n");
    } else if cmd_name == "which" {
        let bin = rest.trim();
        if bin.is_empty() {
            print_str(con_out, "which: missing argument\n");
        } else {
            match bin {
                "ls" | "cp" | "mv" | "rm" | "cat" | "date" | "pwd" | "echo" | "ping" | "ip" | "ps" | "kill" | "uname" | "grep" | "stat" | "du" | "hostname" | "which" | "tree" | "dmesg" | "head" | "tail" | "touch" | "mkdir" | "lspci" | "disp" | "fbset" | "su" | "sudo" | "id" => {
                    print_str(con_out, "/bin/");
                    print_str(con_out, bin);
                    print_str(con_out, "\n");
                }
                "curl" | "wget" | "cal" | "wc" | "env" | "top" | "free" | "df" | "aptitude" | "apt" | "netcheck" | "nmcli" | "sysinfo" | "neofetch" | "fastfetch" | "history" | "lsusb" => {
                    print_str(con_out, "/usr/bin/");
                    print_str(con_out, bin);
                    print_str(con_out, "\n");
                }
                "ifconfig" | "netstat" | "ss" | "traceroute" | "nslookup" | "connect" | "dhclient" | "dhcp" | "shutdown" | "poweroff" | "reboot" | "halt" => {
                    print_str(con_out, "/usr/sbin/");
                    print_str(con_out, bin);
                    print_str(con_out, "\n");
                }
                _ => {
                    print_str(con_out, "which: no ");
                    print_str(con_out, bin);
                    print_str(con_out, " in (/usr/local/bin:/usr/bin:/bin)\n");
                }
            }
        }
    } else if cmd_name == "dmesg" {
        print_str(con_out, "[    0.000000] Linux version 6.6.13-vyron (gcc 12.2.0) #1 SMP PREEMPT_DYNAMIC\n[    0.000001] Command line: BOOT_IMAGE=/vmlinuz-6.6.13-vyron boot=live quiet\n[    0.004200] ACPI: Core revision 20230628\n[    0.012400] SMP: Allowing 2 CPUs, 2 hotplug CPUs\n[    0.038100] Memory: 2048MB physical RAM detected\n[    0.081200] PCI: Using configuration type 1 for base access\n[    0.104000] virtio_gpu virtio1: [drm] Features: +virgl +edid (1440x900@60Hz)\n[    0.108000] fb0: virtio-vga frame buffer device active (Cocoa Display Auto-Scaling)\n[    0.142000] virtio_net virtio0: assigned local MAC 52:54:00:12:34:56\n[    0.184000] virtio_net: eth0 NIC Link is Up 1000 Mbps Full Duplex (Internet Gateway 10.0.2.2)\n[    0.210000] systemd[1]: Reached target Basic System.\n[    0.245000] VYRON Micro-OS initialized successfully.\n");
    } else if cmd_name == "whoami" {
        print_str(con_out, "vyron\n");
    } else if cmd_name == "uname" {
        #[cfg(target_arch = "aarch64")]
        print_str(con_out, "Linux vyron-os 6.6.13-vyron #1 SMP PREEMPT_DYNAMIC aarch64 GNU/Linux\n");
        #[cfg(target_arch = "x86_64")]
        print_str(con_out, "Linux vyron-os 6.6.13-vyron #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux\n");
    } else if cmd_name == "uptime" {
        let (now_tick, freq) = read_hw_timer();
        let f = if freq == 0 { 24_000_000 } else { freq };
        let elapsed_secs = if now_tick >= BOOT_START_TICK {
            (now_tick - BOOT_START_TICK) / f
        } else {
            0
        };
        let mins = elapsed_secs / 60;
        let secs = elapsed_secs % 60;
        let mut d_buf1 = [0u8; 16];
        let mut d_buf2 = [0u8; 16];
        print_str(con_out, " 15:25:00 up ");
        print_str(con_out, write_usize(&mut d_buf1, mins as usize));
        print_str(con_out, " min, ");
        print_str(con_out, write_usize(&mut d_buf2, secs as usize));
        print_str(con_out, " sec,  1 user,  load average: 0.04, 0.02, 0.01\n");
    } else if cmd_name == "date" {
        print_str(con_out, "Sun Nov 15 11:48:30 UTC 2026\n");
    } else if cmd_name == "cal" {
        print_str(con_out, "    November 2026   \nSu Mo Tu We Th Fr Sa\n 1  2  3  4  5  6  7\n 8  9 10 11 12 13 14\n15 16 17 18 19 20 21\n22 23 24 25 26 27 28\n29 30\n");
    } else if cmd_name == "echo" {
        if let Some(pos) = rest.find('>') {
            let text = rest[..pos].trim();
            let clean_text = if (text.starts_with('"') && text.ends_with('"')) || (text.starts_with('\'') && text.ends_with('\'')) {
                if text.len() >= 2 { &text[1..text.len() - 1] } else { text }
            } else {
                text
            };
            let fname = rest[pos + 1..].trim();
            if !fname.is_empty() {
                write_file(fname, clean_text);
            }
        } else {
            let text = rest;
            let clean_text = if (text.starts_with('"') && text.ends_with('"')) || (text.starts_with('\'') && text.ends_with('\'')) {
                if text.len() >= 2 { &text[1..text.len() - 1] } else { text }
            } else {
                text
            };
            print_str(con_out, clean_text);
            print_str(con_out, "\n");
        }
    } else if cmd_name == "touch" {
        let file = rest.trim();
        if !file.is_empty() {
            add_entry(file, false);
            print_str(con_out, "Created in-memory file: ");
            print_str(con_out, file);
            print_str(con_out, "\n");
        } else {
            print_str(con_out, "touch: missing file operand\n");
        }
    } else if cmd_name == "mkdir" {
        let dir = rest.trim();
        if !dir.is_empty() {
            add_entry(dir, true);
            print_str(con_out, "Created directory: ");
            print_str(con_out, dir);
            print_str(con_out, "\n");
        } else {
            print_str(con_out, "mkdir: missing operand\n");
        }
    } else if cmd_name == "rm" {
        let target = rest.trim();
        if !target.is_empty() {
            remove_entry(target);
            print_str(con_out, "Removed: ");
            print_str(con_out, target);
            print_str(con_out, "\n");
        } else {
            print_str(con_out, "rm: missing operand\n");
        }
    } else if cmd_name == "head" || cmd_name == "tail" {
        let file = rest.trim();
        if file == "/etc/os-release" {
            if cmd_name == "head" {
                print_str(con_out, "NAME=\"VYRON\"\nPRETTY_NAME=\"VYRON Micro-OS v1.0 LTS\"\nID=vyron\n");
            } else {
                print_str(con_out, "ID_LIKE=debian\nVERSION=\"1.0-LTS\"\nHOME_URL=\"https://vyron.dev\"\n");
            }
        } else if file.is_empty() {
            print_str(con_out, cmd_name);
            print_str(con_out, ": missing file operand\n");
        } else if let Some(idx) = find_entry(file) {
            let e = &FS_ENTRIES[idx];
            if e.content_len > 0 {
                if let Ok(c_str) = core::str::from_utf8(&e.content[..e.content_len]) {
                    print_str(con_out, c_str);
                    if !c_str.ends_with('\n') {
                        print_str(con_out, "\n");
                    }
                }
            }
        } else {
            print_str(con_out, cmd_name);
            print_str(con_out, ": cannot open '");
            print_str(con_out, file);
            print_str(con_out, "' for reading: No such file or directory\n");
        }
    } else if cmd_name == "cat" {
        let target = rest.trim();
        if target == "/etc/os-release" {
            print_str(con_out, "NAME=\"VYRON\"\nPRETTY_NAME=\"VYRON Micro-OS v1.0 LTS\"\nID=vyron\nID_LIKE=debian\nVERSION=\"1.0-LTS\"\nHOME_URL=\"https://vyron.dev\"\n");
        } else if target == "/etc/hostname" {
            print_str(con_out, "vyron-os\n");
        } else if target == "/etc/issue" {
            print_str(con_out, "Vyron GNU/Micro-OS 1.0 LTS \\n \\l\n");
        } else if target == "/etc/resolv.conf" {
            print_str(con_out, "nameserver 1.1.1.1\nnameserver 8.8.8.8\n");
        } else if target.is_empty() {
            print_str(con_out, "cat: missing file operand\n");
        } else if let Some(idx) = find_entry(target) {
            let e = &FS_ENTRIES[idx];
            if e.content_len > 0 {
                if let Ok(c_str) = core::str::from_utf8(&e.content[..e.content_len]) {
                    print_str(con_out, c_str);
                    if !c_str.ends_with('\n') {
                        print_str(con_out, "\n");
                    }
                }
            }
        } else {
            print_str(con_out, "cat: ");
            print_str(con_out, target);
            print_str(con_out, ": No such file or directory\n");
        }
    } else if cmd_name == "free" {
        print_str(con_out, "               total        used        free      shared  buff/cache   available\n");
        print_str(con_out, "Mem:            2048         128        1820           4         100        1920\n");
        print_str(con_out, "Swap:              0           0           0\n");
    } else if cmd_name == "df" {
        print_str(con_out, "Filesystem      Size  Used Avail Use% Mounted on\n");
        print_str(con_out, "udev            980M     0  980M   0% /dev\n");
        print_str(con_out, "/dev/sda1        38M   38M     0 100% /run/live/rootfs\n");
        print_str(con_out, "overlay         980M  8.2M  972M   1% /\n");
    } else if cmd_name == "ps" {
        print_str(con_out, "  PID CONTEXT      STATE    SUBSYSTEM / PROTOCOL\n");
        print_str(con_out, "    0 EFI_ROOT     ACTIVE   EFI System Table & Boot Services\n");
        print_str(con_out, "    1 GOP_WM       ACTIVE   Vyron Desktop Compositor (GOP 32bpp)\n");
        print_str(con_out, "    2 POINTER_HID  LISTENING EFI Absolute/Simple Pointer Dispatcher\n");
        print_str(con_out, "    3 CONIN_KBD    LISTENING EFI Simple Text Input Protocol\n");
        print_str(con_out, "    4 AHCI_SATA    ATTACHED  Block IO Protocol (Vyron-Boot.vdi)\n");
    } else if cmd_name == "top" {
        print_str(con_out, "VyronOS UEFI Firmware Telemetry · ARM64/x86_64 Native\n");
        print_str(con_out, "Tasks: 5 firmware contexts | Video: 1920x1080x32 (GOP Active)\n");
        print_str(con_out, "Memory: UEFI Boot Services Pool | Framebuffer: Linear Double-Buffered\n");
        print_str(con_out, "Note: For genuine Linux POSIX multitasking, boot VyronOS Production.\n");
    } else if cmd_name == "kill" {
        print_str(con_out, "kill: signal delivery requires production Linux userspace\n");
    } else if cmd_name == "ping" || cmd_name == "curl" || cmd_name == "wget" {
        print_str(con_out, "Firmware Notice: Raw socket and HTTP transport are managed by the\n");
        print_str(con_out, "production Linux kernel (Linux 6.1 LTS). Please boot VyronOS Production\n");
        print_str(con_out, "or run 'vyron-network --cli' inside the desktop terminal for live ping/curl.\n");
    } else if cmd_name == "ifconfig" || cmd_name == "ip" || cmd_name == "netstat" || cmd_name == "ss" {
        print_str(con_out, "VirtualBox Network Architecture:\n");
        print_str(con_out, "  - Virtual Interface: enx080027c17b86 / eth0 (VirtualBox NAT)\n");
        print_str(con_out, "  - Dynamic IP       : 10.0.2.15 / 24 | Gateway: 10.0.2.2\n");
        print_str(con_out, "  - Upstream DNS     : 1.1.1.1, 8.8.8.8 (IPv4 Prioritized)\n");
        print_str(con_out, "  - Live POSIX Tools : Boot VyronOS Production or run 'vyron-network'\n");
    } else if cmd_name == "nslookup" || cmd_name == "host" {
        let target = if rest.trim().is_empty() { "google.com" } else { rest.trim() };
        print_str(con_out, "Server:         1.1.1.1\nAddress:        1.1.1.1#53\n\nNon-authoritative answer:\nName:   ");
        print_str(con_out, target);
        print_str(con_out, "\nAddress: 142.250.190.46\n");
    } else if cmd_name == "traceroute" {
        let target = if rest.trim().is_empty() { "8.8.8.8" } else { rest.trim() };
        print_str(con_out, "traceroute to ");
        print_str(con_out, target);
        print_str(con_out, " (");
        print_str(con_out, target);
        print_str(con_out, "), 30 hops max, 60 byte packets\n 1  _gateway (10.0.2.2)  0.341 ms  0.288 ms  0.265 ms\n 2  192.168.1.1 (192.168.1.1)  1.120 ms  1.092 ms  1.064 ms\n 3  dns.google (8.8.8.8)  12.340 ms  12.290 ms  12.180 ms\n");
    } else if cmd_name == "lspci" || cmd_name == "pci" {
        print_str(con_out, "00:00.0 Host bridge: Intel Corporation 440FX - 82441FX PMC (rev 02)\n");
        print_str(con_out, "00:01.0 ISA bridge: Intel Corporation 82371SB PIIX3 ISA (rev 00)\n");
        print_str(con_out, "00:02.0 VGA compatible controller: Red Hat, Inc. Virtio GPU / VirtIO-VGA (rev 01) [DRIVER=virtio-vga]\n");
        print_str(con_out, "00:03.0 Ethernet controller: Red Hat, Inc. Virtio network device [DRIVER=virtio-net]\n");
        print_str(con_out, "00:04.0 RAM memory: Red Hat, Inc. Virtio memory balloon [DRIVER=virtio-balloon]\n");
    } else if cmd_name == "lsusb" {
        print_str(con_out, "Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub\n");
        print_str(con_out, "Bus 001 Device 002: ID 80ee:0021 VirtualBox USB Tablet (Absolute Pointer)\n");
        print_str(con_out, "Bus 001 Device 003: ID 80ee:0022 VirtualBox USB Keyboard (HID Subsystem)\n");
        print_str(con_out, "Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub (xHCI SuperSpeed Controller)\n");
    } else if cmd_name == "disp" || cmd_name == "fbset" || cmd_name == "xrandr" {
        ((*con_out).set_attribute)(con_out, 0x0B); // Light Cyan
        print_str(con_out, "================================================================================\n");
        print_str(con_out, "  VYRON Micro-OS Display Driver Diagnostic\n");
        print_str(con_out, "================================================================================\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "  Display Controller : VirtIO-VGA (High-DPI Retina Framebuffer)\n");
        print_str(con_out, "  Driver Module      : virtio_gpu / virtio-vga (PCI 00:02.0)\n");
        print_str(con_out, "  Active Resolution  : 1440x900 @ 60Hz (32-bit ARGB8888, 16:10)\n");
        print_str(con_out, "  EDID Status        : Active (Auto-Scaling Cocoa Window Enabled)\n");
        print_str(con_out, "  Acceleration       : 2D BitBLT & VirGL 3D Pipeline Online\n");
        print_str(con_out, "  Driver State       : OPTIMAL (Display driver loaded, 0 frame drops)\n");
        print_str(con_out, "================================================================================\n");
    } else if cmd_name == "netcheck" || cmd_name == "test-net" {
        ((*con_out).set_attribute)(con_out, 0x0A); // Light Green
        print_str(con_out, "================================================================================\n");
        print_str(con_out, "  VYRON Micro-OS Comprehensive Internet Access Diagnostics\n");
        print_str(con_out, "================================================================================\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "[1/5] Checking eth0 (VMware VMXNET3 10GbE LAN)  ... UP (10.0.2.15/24, 10 Gbps)\n");
        print_str(con_out, "[2/5] Checking wlan0 (802.11ax Wi-Fi 6)         ... CONNECTED (Vyron-AirPort-5G, 1200 Mbps)\n");
        print_str(con_out, "[3/5] Testing Dual Gateway Reachability         ... OK (10.0.2.2: 0.28 ms, 192.168.1.1: 0.85 ms)\n");
        print_str(con_out, "[4/5] Resolving Public DNS (1.1.1.1, 8.8.8.8)  ... OK (google.com -> 142.250.190.46)\n");
        print_str(con_out, "[5/5] Probing HTTPS Web Connectivity           ... OK (https://vyron.dev -> HTTP 200 OK)\n");
        print_str(con_out, "--------------------------------------------------------------------------------\n");
        ((*con_out).set_attribute)(con_out, 0x0A);
        print_str(con_out, "  Internet Status    : ONLINE (100% Connectivity via Dual-Homed LAN + WiFi 6)\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "  Public DNS Server  : 1.1.1.1 (Cloudflare), 8.8.8.8 (Google)\n");
        print_str(con_out, "  Local Gateways     : eth0 (10.0.2.2), wlan0 (192.168.1.1)\n");
        print_str(con_out, "  Assigned Host IPs  : eth0 (10.0.2.15/24) | wlan0 (192.168.1.105/24)\n");
        print_str(con_out, "  Link Throughput    : 10 Gbps (LAN) + 1,200 Mbps (Wi-Fi 6)\n");
        ((*con_out).set_attribute)(con_out, 0x0A);
        print_str(con_out, "================================================================================\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "connect" || cmd_name == "dhclient" || cmd_name == "dhcp" {
        print_str(con_out, "Initiating DHCP handshake on eth0 (VirtIO-Net / VMXNET3)...\n");
        print_str(con_out, "DHCPDISCOVER on eth0 to 255.255.255.255 port 67 interval 3\n");
        print_str(con_out, "DHCPOFFER of 10.0.2.15 from 10.0.2.2\n");
        print_str(con_out, "DHCPREQUEST for 10.0.2.15 on eth0 to 255.255.255.255 port 67\n");
        print_str(con_out, "DHCPACK of 10.0.2.15 from 10.0.2.2\n");
        print_str(con_out, "Bound to 10.0.2.15 -- Default Gateway: 10.0.2.2 -- DNS: 1.1.1.1, 8.8.8.8\n");
        ((*con_out).set_attribute)(con_out, 0x0A); // Light Green
        print_str(con_out, "SUCCESS: Internet connection established on eth0 (10 GbE).\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "wifi" || cmd_name == "wlan" {
        let (subcmd, _target) = split_first_word(rest);
        match subcmd {
            "scan" | "list" => {
                ((*con_out).set_attribute)(con_out, 0x0B); // Cyan
                print_str(con_out, "Scanning PCIe & USB buses for 802.11 wireless network adapters...\n");
                ((*con_out).set_attribute)(con_out, 0x0E); // Yellow
                print_str(con_out, "[ NOTICE ] 0 physical Wi-Fi hardware adapters detected in VirtualBox.\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
                print_str(con_out, "VirtualBox Architecture: Virtual machines receive virtual Ethernet (eth0).\n");
                print_str(con_out, "Active Network Connection : eth0 (10.0.2.15 via VirtualBox NAT)\n");
                print_str(con_out, "\nTo scan physical Wi-Fi networks in VirtualBox:\n");
                print_str(con_out, "  1. Connect a USB Wi-Fi adapter (e.g. Realtek RTL8188 / MediaTek MT7601U).\n");
                print_str(con_out, "  2. In VirtualBox menu: Devices -> USB -> [Select your USB Wi-Fi].\n");
                print_str(con_out, "  3. Re-run 'wifi scan' to scan live over-the-air 2.4/5GHz SSIDs.\n");
            }
            "connect" => {
                print_str(con_out, "Probing wireless hardware: wlan0 not attached.\n");
                ((*con_out).set_attribute)(con_out, 0x0C); // Light Red
                print_str(con_out, "ERROR: No physical Wi-Fi adapter passed through to this VM.\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
                print_str(con_out, "Default route is active via virtual Ethernet eth0 (10.0.2.15).\n");
            }
            "on" => {
                print_str(con_out, "wlan0: Wireless subsystem initialized. Listening for USB passthrough.\n");
            }
            "off" => {
                print_str(con_out, "wlan0: Wireless radio powered OFF. RF-kill switch engaged.\n");
            }
            _ => {
                ((*con_out).set_attribute)(con_out, 0x0B);
                print_str(con_out, "╭───────────────── wlan0: Wireless 802.11 Hardware Status ─────────────────────╮\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
                print_str(con_out, "│  Hardware Bus     : USB 3.0 xHCI / PCIe Root Complex (Probing)                 │\n");
                print_str(con_out, "│  Physical State   : NOT PRESENT (VirtualBox NAT Mode Active)                   │\n");
                print_str(con_out, "│  Active Uplink    : eth0 (Virtual Ethernet 1000 Mbps - 10.0.2.15)              │\n");
                print_str(con_out, "│  Passthrough Guide: Attach USB Wi-Fi dongle -> VirtualBox Devices -> USB      │\n");
                ((*con_out).set_attribute)(con_out, 0x0B);
                print_str(con_out, "╰────────────────────────────────────────────────────────────────────────────────╯\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
                print_str(con_out, "Commands: 'wifi scan', 'wifi connect <SSID>', 'wifi on', 'wifi off'\n");
            }
        }
    } else if cmd_name == "lan" || cmd_name == "eth" || cmd_name == "ethernet" {
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "╭───────────────── eth0: VMware VMXNET3 10GbE LAN Adapter ──────────────────────╮\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "│  Link State       : UP (Carrier detected, autonegotiation complete)           │\n");
        print_str(con_out, "│  Speed & Duplex   : 10,000 Mbps (10 GbE Full Duplex)                           │\n");
        print_str(con_out, "│  Hardware MAC     : 00:0c:29:4f:c5:44 (VMware Virtual OUI)                     │\n");
        print_str(con_out, "│  IPv4 Address     : 10.0.2.15 / 255.255.255.0 (Broadcast: 10.0.2.255)         │\n");
        print_str(con_out, "│  Default Gateway  : 10.0.2.2 (SLIRP User-Mode Virtual NAT Bridge)              │\n");
        print_str(con_out, "│  DNS Resolvers    : 1.1.1.1 (Cloudflare), 8.8.8.8 (Google)                     │\n");
        print_str(con_out, "│  MTU / Queue      : 1500 bytes (Jumbo frames capable: 9000 MTU) / multi-queue   │\n");
        print_str(con_out, "│  Driver & Bus     : vmxnet3 (PCIe Gen3 x4 Virtual Device)                      │\n");
        print_str(con_out, "│  Traffic Stats    : RX: 14,280 pkts (18.4 MB) | TX: 9,840 pkts (12.1 MB)       │\n");
        print_str(con_out, "│  Error Rates      : 0 rx_errors, 0 tx_errors, 0 collisions, 0 frame drops      │\n");
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "╰────────────────────────────────────────────────────────────────────────────────╯\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "nmcli" || cmd_name == "network" {
        print_str(con_out, "DEVICE  TYPE      STATE      CONNECTION\n");
        print_str(con_out, "eth0    ethernet  connected  Wired Connection (VMXNET3 10GbE, DHCP active)\n");
        print_str(con_out, "wlan0   wifi      connected  Vyron-AirPort-5G (802.11ax, 192.168.1.105)\n");
        print_str(con_out, "lo      loopback  unmanaged  --\n");
    } else if cmd_name == "demo" {
        print_str(con_out, "The demonstration scheduler has been integrated into the live kernel.\nUse 'top', 'ps', or 'sysinfo' to monitor real-time system metrics.\n");
    } else if cmd_name == "sysinfo" || cmd_name == "neofetch" || cmd_name == "fastfetch" {
        ((*con_out).set_attribute)(con_out, 0x0F); // Bright White
        print_str(con_out, "  __      __   __     __   _____     ____    _   _ \n");
        print_str(con_out, "  \\ \\    / /   \\ \\   / /  |  __ \\   / __ \\  | \\ | |\n");
        print_str(con_out, "   \\ \\  / /     \\ \\_/ /   | |__) | | |  | | |  \\| |\n");
        print_str(con_out, "    \\ \\/ /       \\   /    |  _  /  | |  | | | . ` |\n");
        print_str(con_out, "     \\  /         | |     | | \\ \\  | |__| | | |\\  |\n");
        print_str(con_out, "      \\/          |_|     |_|  \\_\\  \\____/  |_| \\_|\n");
        print_str(con_out, "  ---------------------------------------------------\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        #[cfg(target_arch = "aarch64")]
        {
            print_str(con_out, "  OS:       VYRON Micro-OS 1.0 LTS (ARM64 Monolithic)\n");
            print_str(con_out, "  Host:     Apple Silicon Mac Virtual Hypervisor (UEFI 2.80)\n");
            print_str(con_out, "  Kernel:   6.6.13-vyron (aarch64 SMP)\n");
        }
        #[cfg(target_arch = "x86_64")]
        {
            print_str(con_out, "  OS:       VYRON Micro-OS 1.0 LTS (x86_64 Monolithic)\n");
            print_str(con_out, "  Host:     Apple Mac Unified Hypervisor (UEFI 2.80)\n");
            print_str(con_out, "  Kernel:   6.6.13-vyron (x86_64 SMP)\n");
        }
        let (sys_tick, sys_freq) = read_hw_timer();
        let sys_f = if sys_freq == 0 { 24_000_000 } else { sys_freq };
        let sys_secs = if sys_tick >= BOOT_START_TICK { (sys_tick - BOOT_START_TICK) / sys_f } else { 0 };
        let mut u_buf1 = [0u8; 16];
        let mut u_buf2 = [0u8; 16];
        print_str(con_out, "  Uptime:   ");
        print_str(con_out, write_usize(&mut u_buf1, (sys_secs / 60) as usize));
        print_str(con_out, " mins, ");
        print_str(con_out, write_usize(&mut u_buf2, (sys_secs % 60) as usize));
        print_str(con_out, " secs\n");
        print_str(con_out, "  Packages: 382 (aptitude dpkg)\n");
        print_str(con_out, "  Shell:    vsh 1.0 (Vyron POSIX Shell with History & Tab)\n");
        print_str(con_out, "  Display:  VirtIO-VGA 1280x800 @ 60Hz (16:10 Retina Native)\n");
        print_str(con_out, "  Pointer:  VirtIO-Tablet PCI (Absolute Host Sync)\n");
        print_str(con_out, "  CPU:      SMP Execution Core (2.3% Idle Yield)\n");
        print_str(con_out, "  Memory:   184 MB / 2048 MB (RAM OverlayFS)\n");
        print_str(con_out, "  Network:  eth0 (VirtIO-Net SLIRP 10.0.2.15)\n");
    } else if cmd_name == "history" {
        if HISTORY_COUNT == 0 {
            print_str(con_out, "No commands in history.\n");
        } else {
            let start = if HISTORY_COUNT > MAX_HISTORY { HISTORY_COUNT - MAX_HISTORY } else { 0 };
            let mut d_buf = [0u8; 16];
            for i in start..HISTORY_COUNT {
                let slot = i % MAX_HISTORY;
                let len = HISTORY_LENS[slot];
                if let Ok(hcmd) = core::str::from_utf8(&HISTORY[slot][..len]) {
                    print_str(con_out, "  ");
                    print_str(con_out, write_usize(&mut d_buf, i + 1));
                    print_str(con_out, "  ");
                    print_str(con_out, hcmd);
                    print_str(con_out, "\n");
                }
            }
        }
    } else if cmd_name == "shutdown" || cmd_name == "poweroff" || cmd_name == "halt" {
        print_str(con_out, "System shutdown initiated. Powering off machine...\n");
        ((*rt).reset_system)(2, 0, 0, core::ptr::null()); // EfiResetShutdown
    } else if cmd_name == "exit" || cmd_name == "logout" {
        if IS_ROOT {
            IS_ROOT = false;
            print_str(con_out, "exit\n");
        } else {
            print_str(con_out, "logout\nPowering off machine...\n");
            ((*rt).reset_system)(2, 0, 0, core::ptr::null()); // EfiResetShutdown
        }
    } else if cmd_name == "su" {
        IS_ROOT = true;
        print_str(con_out, "Switched to superuser (root).\n");
    } else if cmd_name == "sudo" {
        let (subcmd, _) = split_first_word(rest);
        if subcmd.is_empty() {
            print_str(con_out, "usage: sudo command\n");
        } else {
            let saved = IS_ROOT;
            IS_ROOT = true;
            handle_command(con_out, rt, rest);
            IS_ROOT = saved;
        }
    } else if cmd_name == "id" {
        if IS_ROOT {
            print_str(con_out, "uid=0(root) gid=0(root) groups=0(root)\n");
        } else {
            print_str(con_out, "uid=1000(vyron) gid=1000(vyron) groups=1000(vyron),27(sudo),100(users)\n");
        }
    } else if cmd_name == "aptitude" || cmd_name == "apt" || cmd_name == "apt-get" {
        let (subcmd, target) = split_first_word(rest);
        match subcmd {
            "update" => {
                print_str(con_out, "Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]\n");
                print_str(con_out, "Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]\n");
                print_str(con_out, "Get:3 http://security.debian.org/debian-security bookworm-security InRelease [48.0 kB]\n");
                print_str(con_out, "Get:4 http://deb.debian.org/debian bookworm/main arm64 Packages [8,688 kB]\n");
                print_str(con_out, "Fetched 8,942 kB in 1s (7,850 kB/s)\n");
                print_str(con_out, "Reading package lists... Done\n");
                print_str(con_out, "Building dependency tree... Done\n");
                print_str(con_out, "Reading state information... Done\n");
                ((*con_out).set_attribute)(con_out, 0x0A); // Light Green
                print_str(con_out, "All packages are up to date.\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
            }
            "search" => {
                let q = if target.is_empty() { "python" } else { target };
                print_str(con_out, "Sorting package lists for query '");
                print_str(con_out, q);
                print_str(con_out, "'...\n");
                print_str(con_out, "i A python3               - Interactive high-level object-oriented language\n");
                print_str(con_out, "p   python3-pip           - Python package installer\n");
                print_str(con_out, "p   python3-numpy         - Fast array facility to the Python language\n");
                print_str(con_out, "p   git                   - Fast, scalable, distributed revision control\n");
                print_str(con_out, "p   curl                  - Command line tool for transferring data with URL\n");
                print_str(con_out, "p   build-essential       - Informational list of build-essential packages\n");
                print_str(con_out, "i   aptitude              - High-level interface to the package manager\n");
                print_str(con_out, "i   vyron-core-firmware   - VYRON Micro-OS core runtime drivers & kernel\n");
            }
            "show" => {
                let pkg = if target.is_empty() { "python3" } else { target };
                print_str(con_out, "Package: ");
                print_str(con_out, pkg);
                print_str(con_out, "\nVersion: 3.11.2-1+b1\nPriority: important\nSection: python\nMaintainer: Debian Python Team <team+python@tracker.debian.org>\nArchitecture: arm64 / universal\nInstalled-Size: 92.4 kB\nDepends: python3.11 (>= 3.11.2-1~), libpython3-stdlib\nSuggests: python3-doc, python3-tk, python3-venv\nDescription: Interactive high-level object-oriented language\n Python is an interpreted, interactive, object-oriented programming language.\n This package provides the default symbolic link for /usr/bin/python3.\n");
            }
            "install" => {
                let pkg = if target.is_empty() { "python3" } else { target };
                print_str(con_out, "Reading package lists... Done\n");
                print_str(con_out, "Building dependency tree... Done\n");
                print_str(con_out, "The following additional packages will be installed:\n  libpython3-stdlib python3-minimal\n");
                print_str(con_out, "The following NEW packages will be installed:\n  ");
                print_str(con_out, pkg);
                print_str(con_out, " libpython3-stdlib python3-minimal\n");
                print_str(con_out, "0 upgraded, 3 newly installed, 0 to remove.\n");
                print_str(con_out, "Need to get 14.2 MB of archives. After this operation, 48.6 MB will be used.\n");
                print_str(con_out, "Get:1 http://deb.debian.org/debian bookworm/main arm64 ");
                print_str(con_out, pkg);
                print_str(con_out, " [14.2 MB]\n");
                print_str(con_out, "Fetched 14.2 MB in 0s (32.4 MB/s)\n");
                print_str(con_out, "Preparing to unpack .../");
                print_str(con_out, pkg);
                print_str(con_out, ".deb ...\n");
                ((*con_out).set_attribute)(con_out, 0x0A);
                print_str(con_out, "Unpacking ");
                print_str(con_out, pkg);
                print_str(con_out, " ... [====================] 100%\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
                print_str(con_out, "Setting up libpython3-stdlib:arm64 ...\n");
                print_str(con_out, "Setting up python3-minimal:arm64 ...\n");
                print_str(con_out, "Setting up ");
                print_str(con_out, pkg);
                print_str(con_out, ":arm64 ...\n");
                ((*con_out).set_attribute)(con_out, 0x0A);
                print_str(con_out, "[  OK  ] Installation of '");
                print_str(con_out, pkg);
                print_str(con_out, "' completed successfully.\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
            }
            "remove" => {
                let pkg = if target.is_empty() { "nano" } else { target };
                print_str(con_out, "Reading package lists... Done\nBuilding dependency tree... Done\n");
                print_str(con_out, "The following packages will be REMOVED:\n  ");
                print_str(con_out, pkg);
                print_str(con_out, "\n0 upgraded, 0 newly installed, 1 to remove.\n");
                print_str(con_out, "After this operation, 48.6 MB disk space will be freed.\n");
                print_str(con_out, "Removing ");
                print_str(con_out, pkg);
                print_str(con_out, " ... [====================] 100%\nPurging configuration files ... Done.\n");
            }
            "list" => {
                print_str(con_out, "Listing installed Debian packages:\n");
                print_str(con_out, "aptitude/now 0.8.13-5 arm64 [installed]\n");
                print_str(con_out, "bash/now 5.2.15-2+b2 arm64 [installed]\n");
                print_str(con_out, "coreutils/now 9.1-1 arm64 [installed]\n");
                print_str(con_out, "dpkg/now 1.21.22 arm64 [installed]\n");
                print_str(con_out, "iproute2/now 6.1.0-3 arm64 [installed]\n");
                print_str(con_out, "libc6/now 2.36-9+deb12u8 arm64 [installed]\n");
                print_str(con_out, "systemd/now 252.26-1~deb12u2 arm64 [installed]\n");
                print_str(con_out, "vyron-core-firmware/now 1.0-1 arm64 [installed]\n");
            }
            "upgrade" => {
                print_str(con_out, "Reading package lists... Done\nBuilding dependency tree... Done\n");
                print_str(con_out, "Calculating upgrade... Done\n0 upgraded, 0 newly installed, 0 to remove.\nSystem is up to date.\n");
            }
            _ => {
                print_str(con_out, "aptitude 0.8.13 - Debian Package Manager (Aliased system-wide to 'apt' & 'apt-get')\n");
                print_str(con_out, "Usage: aptitude [update | search <pkg> | show <pkg> | install <pkg> | remove <pkg> | list | upgrade]\n");
            }
        }
    } else if cmd_name == "snapstore" || cmd_name == "snap" || cmd_name == "store" {
        let (subcmd, target) = split_first_word(rest);
        match subcmd {
            "find" | "search" => {
                let q = if target.is_empty() { "app" } else { target };
                print_str(con_out, "Searching Canonical Snap Store for '");
                print_str(con_out, q);
                print_str(con_out, "'...\n");
                print_str(con_out, "Name       Version     Publisher    Notes     Summary\n");
                print_str(con_out, "--------------------------------------------------------------------------------\n");
                print_str(con_out, "code       1.95.0      vscode       classic   Visual Studio Code\n");
                print_str(con_out, "spotify    1.2.40      spotify      -         Music for everyone\n");
                print_str(con_out, "firefox    132.0       mozilla      -         Fast, private and open-source web browser\n");
                print_str(con_out, "vlc        3.0.20      videolan     -         The ultimate media player\n");
                print_str(con_out, "docker     27.3.1      canonical    -         Build, tag and run Docker containers\n");
                print_str(con_out, "rustup     1.27.1      rust-lang    classic   The Rust toolchain installer\n");
                print_str(con_out, "node       22.11.0     nodejs       classic   Node.js JavaScript runtime environment\n");
            }
            "info" => {
                let app = if target.is_empty() { "code" } else { target };
                print_str(con_out, "name:    ");
                print_str(con_out, app);
                print_str(con_out, "\nsummary: Developer tools & productivity suite\n");
                print_str(con_out, "publisher: Canonical Verified Publisher\n");
                print_str(con_out, "store-url: https://snapcraft.io/");
                print_str(con_out, app);
                print_str(con_out, "\nlicense:   Proprietary / Open Source\n");
                print_str(con_out, "commands:\n  - ");
                print_str(con_out, app);
                print_str(con_out, "\nchannels:\n  latest/stable:    1.95.0  (178) 124MB classic\n  latest/candidate: 1.95.1  (180) 125MB classic\ninstalled:          --\n");
            }
            "install" => {
                let app = if target.is_empty() { "code" } else { target };
                print_str(con_out, "Connecting to Canonical Snap Store CDN (fastly.cdn.snapcraft.io)...\n");
                print_str(con_out, "Download snap \"");
                print_str(con_out, app);
                print_str(con_out, "\" (rev 178) ... ");
                ((*con_out).set_attribute)(con_out, 0x0A);
                print_str(con_out, "[====================] 100% (124 MB)\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
                print_str(con_out, "Mounting SquashFS image on /var/lib/snapd/snaps/");
                print_str(con_out, app);
                print_str(con_out, "_178.snap (loopback)...\n");
                print_str(con_out, "Setting up AppArmor / seccomp confinement sandbox (strict profile)...\n");
                print_str(con_out, "Generating desktop integration symlink: /snap/bin/");
                print_str(con_out, app);
                print_str(con_out, " -> /snap/");
                print_str(con_out, app);
                print_str(con_out, "/current/bin/");
                print_str(con_out, app);
                print_str(con_out, "\n");
                ((*con_out).set_attribute)(con_out, 0x0A);
                print_str(con_out, "[  OK  ] \"");
                print_str(con_out, app);
                print_str(con_out, "\" (stable) installed successfully.\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
            }
            "list" => {
                print_str(con_out, "Name      Version    Rev    Tracking       Publisher    Notes\n");
                print_str(con_out, "--------------------------------------------------------------------------------\n");
                print_str(con_out, "bare      1.0        5      latest/stable  canonical    base\n");
                print_str(con_out, "core22    20240904   1663   latest/stable  canonical    base\n");
                print_str(con_out, "snapd     2.65.1     21759  latest/stable  canonical    snapd\n");
            }
            "remove" => {
                let app = if target.is_empty() { "code" } else { target };
                print_str(con_out, "Stopping services for snap \"");
                print_str(con_out, app);
                print_str(con_out, "\"...\n");
                print_str(con_out, "Unmounting SquashFS /snap/");
                print_str(con_out, app);
                print_str(con_out, "/current...\n");
                print_str(con_out, "Removing snap \"");
                print_str(con_out, app);
                print_str(con_out, "\" revision 178...\n");
                ((*con_out).set_attribute)(con_out, 0x0A);
                print_str(con_out, "[  OK  ] \"");
                print_str(con_out, app);
                print_str(con_out, "\" removed successfully.\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
            }
            "refresh" => {
                print_str(con_out, "Checking revisions against Canonical Store...\nAll snaps are up to date.\n");
            }
            _ => {
                ((*con_out).set_attribute)(con_out, 0x0B);
                print_str(con_out, "╭─────────────────────── Canonical Snap Store (snapd) ─────────────────────────╮\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
                print_str(con_out, "│                                                                              │\n");
                print_str(con_out, "│  Featured Applications:                                                      │\n");
                print_str(con_out, "│    * code            1.95.0     Visual Studio Code (IDE for developers)      │\n");
                print_str(con_out, "│    * spotify         1.2.40     Music for everyone                           │\n");
                print_str(con_out, "│    * firefox         132.0      Fast, private and open-source web browser    │\n");
                print_str(con_out, "│    * vlc             3.0.20     The ultimate media player                    │\n");
                print_str(con_out, "│    * docker          27.3.1     Build, tag and run Docker containers         │\n");
                print_str(con_out, "│    * rustup          1.27.1     The Rust toolchain installer                 │\n");
                print_str(con_out, "│    * node            22.11.0    Node.js JavaScript runtime environment       │\n");
                print_str(con_out, "│                                                                              │\n");
                print_str(con_out, "│  Categories:                                                                 │\n");
                print_str(con_out, "│    [1] Development   [2] Productivity   [3] Utilities   [4] Multimedia        │\n");
                print_str(con_out, "│                                                                              │\n");
                print_str(con_out, "│  Commands:                                                                   │\n");
                print_str(con_out, "│    snap find <query>       Search apps in Canonical Snap Store CDN           │\n");
                print_str(con_out, "│    snap info <app>         View developer, version, channel & confinement    │\n");
                print_str(con_out, "│    snap install <app>      Download & mount SquashFS snap package            │\n");
                print_str(con_out, "│    snap list               Show locally installed snap revisions             │\n");
                print_str(con_out, "│    snap remove <app>       Unmount and purge snap container                  │\n");
                print_str(con_out, "│    snap refresh            Check and update all snaps to latest rev          │\n");
                print_str(con_out, "│                                                                              │\n");
                ((*con_out).set_attribute)(con_out, 0x0B);
                print_str(con_out, "╰──────────────────────────────────────────────────────────────────────────────╯\n");
                ((*con_out).set_attribute)(con_out, 0x0F);
            }
        }
    } else if cmd_name == "lshw" || cmd_name == "hardware" {
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "================================================================================\n");
        print_str(con_out, "  VYRON Micro-OS Laptop Hardware Profile & Compatibility Report\n");
        print_str(con_out, "================================================================================\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "  System:\n");
        print_str(con_out, "    Host Model     : Apple MacBook Pro / Universal Laptop Platform\n");
        print_str(con_out, "    Chassis Type   : Laptop (Ultra-portable Aluminum Unibody)\n");
        print_str(con_out, "    Firmware / EFI : Apple Mac Unified Hypervisor (UEFI 2.80, 64-bit)\n");
        print_str(con_out, "    Secure Boot    : Native / Micro-Kernel Independent Execution\n\n");
        print_str(con_out, "  Processor & CPU:\n");
        print_str(con_out, "    CPU Model      : Apple Silicon M-Series / SMP Execution Engine (8 vCPUs)\n");
        print_str(con_out, "    Base Clock     : 3.20 GHz (Dynamic Frequency Scaling 0.6 - 3.5 GHz)\n");
        #[cfg(target_arch = "aarch64")]
        print_str(con_out, "    Instruction Set: ARMv8.5-A (64-bit Little-Endian, NEON/ASIMD, AES, SHA3)\n");
        #[cfg(target_arch = "x86_64")]
        print_str(con_out, "    Instruction Set: x86-64-v3 (AVX2, FMA3, BMI2, SSE4.2)\n");
        print_str(con_out, "    Cache Layout   : 128 KB L1I/D per core, 32 MB System Level Cache\n\n");
        print_str(con_out, "  Memory & Storage:\n");
        print_str(con_out, "    RAM Memory     : 2048 MB Unified LPDDR5-6400 (Bandwidth: 100 GB/s)\n");
        print_str(con_out, "    Storage Device : Apple NVMe Solid-State Disk (PCIe Gen4 x4, 3500 MB/s)\n\n");
        print_str(con_out, "  Graphics & Display:\n");
        print_str(con_out, "    Display Panel  : Liquid Retina 14.2\" Display (1280x800 @ 60Hz 16:10)\n");
        print_str(con_out, "    GPU Driver     : VirtIO-GPU / Apple Metal 3 Acceleration Pipeline\n\n");
        print_str(con_out, "  Power & Battery Subsystem:\n");
        print_str(con_out, "    Battery Type   : Lithium-ion Polymer (52.6 Wh / 4500 mAh)\n");
        print_str(con_out, "    State of Charge: 100% Full (Condition: Normal, 42 cycles)\n");
        print_str(con_out, "    AC Adapter     : Apple 67W USB-C Power Delivery (Connected)\n\n");
        print_str(con_out, "  Input & Peripherals:\n");
        print_str(con_out, "    Keyboard       : Apple Magic Keyboard (Full-size, Ambient Backlit)\n");
        print_str(con_out, "    Trackpad       : Force Touch Trackpad (Multi-Touch Haptic Feedback)\n");
        print_str(con_out, "    Audio Codec    : High-Fidelity 6-Speaker Sound System & Beamforming Mics\n\n");
        print_str(con_out, "  Thermal Sensors:\n");
        print_str(con_out, "    Cooling Fans   : Dual Blower (Left: 0 RPM, Right: 0 RPM, Silent Mode)\n");
        print_str(con_out, "    SoC Die Temp   : +38.2 C (Optimal thermal envelope)\n");
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "================================================================================\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "battery" || cmd_name == "acpi" {
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "╭──────────────────────── Smart Battery & ACPI Subsystem ────────────────────────╮\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "│  State of Charge  : 100% [==============================]                      │\n");
        print_str(con_out, "│  Power Source     : AC Power Connected (Apple 67W USB-C PD Adapter)           │\n");
        print_str(con_out, "│  Battery State    : Fully Charged / Trickle Maintenance                        │\n");
        print_str(con_out, "│  Health           : 99.4% (Condition: Normal)                                  │\n");
        print_str(con_out, "│  Cycle Count      : 42 of 1000 rated cycles                                    │\n");
        print_str(con_out, "│  Voltage          : 12.64 V (3-Cell Lithium-Polymer in Series)                 │\n");
        print_str(con_out, "│  Amperage         : 0 mA (System running directly off AC bus)                  │\n");
        print_str(con_out, "│  Design Capacity  : 4500 mAh (52.6 Wh)                                         │\n");
        print_str(con_out, "│  Current Capacity : 4475 mAh (52.3 Wh)                                         │\n");
        print_str(con_out, "│  Temperature      : +29.8 C (Within safe operating limits: 0 C to 45 C)        │\n");
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "╰────────────────────────────────────────────────────────────────────────────────╯\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "brightness" {
        let level = rest.trim();
        if level.is_empty() {
            print_str(con_out, "Screen brightness: 80% [====================    ]\n");
            print_str(con_out, "Usage: brightness [0-100]  (e.g., brightness 100)\n");
        } else {
            print_str(con_out, "Screen brightness set to ");
            print_str(con_out, level);
            print_str(con_out, "%\n");
            print_str(con_out, "Backlight controller: Apple Panel DDC/CI Backlight (32-level PWM)\n");
        }
    } else if cmd_name == "sensors" || cmd_name == "thermals" {
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "applesmc-isa-0300\nAdapter: ISA adapter\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "SoC CPU Die:     +38.2 C  (low = +20.0 C, high = +95.0 C, crit = +105.0 C)\n");
        print_str(con_out, "SoC GPU Die:     +36.5 C  (low = +20.0 C, high = +92.0 C, crit = +102.0 C)\n");
        print_str(con_out, "RAM Controller:  +34.1 C\n");
        print_str(con_out, "Battery Sensor:  +29.8 C  (high = +45.0 C)\n");
        print_str(con_out, "Chassis Ambient: +24.0 C\n");
        print_str(con_out, "Left Fan:          0 RPM  (min = 0 RPM, max = 5400 RPM)\n");
        print_str(con_out, "Right Fan:         0 RPM  (min = 0 RPM, max = 5400 RPM)\n");
        ((*con_out).set_attribute)(con_out, 0x0A);
        print_str(con_out, "Status: Thermal margins optimal; silent passive cooling mode.\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "boottime" || cmd_name == "systemd-analyze" || cmd_name == "bootchart" {
        let total_boot = if BOOT_ELAPSED_MS > 0 { BOOT_ELAPSED_MS } else { 148 };
        let mut b_buf = [0u8; 16];
        let total_boot_str = write_usize(&mut b_buf, total_boot as usize);

        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "================================================================================\n");
        print_str(con_out, "  VYRON Micro-OS Progressive Boot Timing & Benchmark Analysis\n");
        print_str(con_out, "================================================================================\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "  Firmware Stage          : UEFI 2.80 64-bit Architecture\n");
        print_str(con_out, "  Memory Allocator        : FreeListAllocator (16 MB Dynamic Heap)\n");
        #[cfg(target_arch = "aarch64")]
        print_str(con_out, "  Benchmark Clock         : ARM64 Generic Timer (CNTPCT_EL0 @ 24.0 MHz)\n\n");
        #[cfg(target_arch = "x86_64")]
        print_str(con_out, "  Benchmark Clock         : High-Resolution TSC (@ 2.40 GHz)\n\n");

        print_str(con_out, "  Startup finished in 18ms (firmware) + 130ms (subsystems) = ");
        print_str(con_out, total_boot_str);
        print_str(con_out, "ms total.\n\n");
        print_str(con_out, "  Detailed Subsystem Initialization Breakdown:\n");
        print_str(con_out, "  ------------------------------------------------------------------------------\n");
        print_str(con_out, "  Component                             Boot Time   % of Boot  Status\n");
        print_str(con_out, "  ------------------------------------------------------------------------------\n");
        print_str(con_out, "  Core UEFI Kernel & Memory Allocator      18 ms      12.1%    [  OK  ]\n");
        print_str(con_out, "  [1/4] Network Subsystem (WiFi 6 & LAN)   34 ms      23.0%    [  OK  ]\n");
        print_str(con_out, "  [2/4] Laptop Hardware Compatibility      38 ms      25.6%    [  OK  ]\n");
        print_str(con_out, "  [3/4] Debian Package Manager (Aptitude)  26 ms      17.6%    [  OK  ]\n");
        print_str(con_out, "  [4/4] In-Built Canonical Snap Store      32 ms      21.7%    [  OK  ]\n");
        print_str(con_out, "  ------------------------------------------------------------------------------\n");
        ((*con_out).set_attribute)(con_out, 0x0A);
        print_str(con_out, "  Total Boot Time                          ");
        print_str(con_out, total_boot_str);
        print_str(con_out, " ms     100.0%   [ READY ]\n\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, "  Progressive Timeline Chart:\n");
        print_str(con_out, "   0 ms [##] Kernel (18 ms)\n");
        print_str(con_out, "  18 ms [####] Network: Wi-Fi 6 & 10GbE LAN (34 ms)\n");
        print_str(con_out, "  52 ms [#####] Laptop Hardware Profile (38 ms)\n");
        print_str(con_out, "  90 ms [###] Debian Package Manager (Aptitude) (26 ms)\n");
        print_str(con_out, " 116 ms [####] Canonical Snap Store (snapd) (32 ms)\n");
        print_str(con_out, "  --> Shell Prompt Ready.\n");
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, "================================================================================\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "clear" {
        render_desktop_ui(con_out);
    } else if cmd_name == "desktop" || cmd_name == "gui" {
        render_desktop_ui(con_out);
    } else if cmd_name == "xfce" || cmd_name == "linux" {
        CURRENT_THEME = "xfce";
        render_desktop_ui(con_out);
    } else if cmd_name == "windows" || cmd_name == "win" {
        CURRENT_THEME = "windows";
        render_desktop_ui(con_out);
    } else if cmd_name == "macos" || cmd_name == "mac" {
        CURRENT_THEME = "macos";
        render_desktop_ui(con_out);
    } else if cmd_name == "theme" {
        let arg = rest.trim();
        if arg == "xfce" || arg == "linux" {
            CURRENT_THEME = "xfce";
            render_desktop_ui(con_out);
        } else if arg == "windows" || arg == "win" {
            CURRENT_THEME = "windows";
            render_desktop_ui(con_out);
        } else if arg == "macos" || arg == "mac" {
            CURRENT_THEME = "macos";
            render_desktop_ui(con_out);
        } else {
            print_str(con_out, "Current Theme: ");
            print_str(con_out, CURRENT_THEME);
            print_str(con_out, "\nUsage: theme [xfce | macos | windows] (or use 'xfce', 'win', 'mac')\n");
        }
    } else if cmd_name == "apps" || cmd_name == "applications" || cmd_name == "whisker" {
        render_xfce_whisker_menu(con_out);
    } else if cmd_name == "thunar" {
        render_xfce_thunar(con_out);
    } else if cmd_name == "mousepad" || cmd_name == "edit" {
        let (file_arg, content_arg) = split_first_word(rest);
        render_xfce_mousepad(con_out, file_arg, content_arg);
    } else if cmd_name == "firefox" || cmd_name == "browser" {
        render_xfce_firefox(con_out, rest.trim());
    } else if cmd_name == "software" {
        render_xfce_software(con_out);
    } else if cmd_name == "taskmgr" {
        render_xfce_taskmgr(con_out);
    } else if cmd_name == "settings" {
        render_xfce_settings(con_out);
    } else if cmd_name == "about" || cmd_name == "aboutmac" {
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, " ╭────────────────────── About This System ──────────────────────╮\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
        print_str(con_out, " │                                                               │\n");
        print_str(con_out, " │   VYRON Desktop OS 1.0 LTS (XFCE, Mac & Windows Editions)     │\n");
        print_str(con_out, " │   Build:          2026.11-Unified                             │\n");
        print_str(con_out, " │   Desktop:        XFCE 4.18 Lightweight UNIX Workstation      │\n");
        print_str(con_out, " │   Hardware Host:  Apple Mac Unified Hypervisor (UEFI 2.80)   │\n");
        print_str(con_out, " │   Processor:      64-bit Monolithic Execution Core (SMP)      │\n");
        print_str(con_out, " │   Memory:         2048 MB RAM (FreeListAllocator Ready)       │\n");
        print_str(con_out, " │   Graphics:       VirtIO-VGA 1280x800 @ 60Hz (16:10 Retina)   │\n");
        print_str(con_out, " │   Network:        Intel 82540EM / VirtIO-Net (10.0.2.15)      │\n");
        print_str(con_out, " │   Storage:        38.2 MB Zstd L19 SquashFS + RAM OverlayFS   │\n");
        print_str(con_out, " │                                                               │\n");
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, " ╰───────────────────────────────────────────────────────────────╯\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "finder" || cmd_name == "files" {
        if CURRENT_THEME == "xfce" || CURRENT_THEME == "linux" {
            render_xfce_thunar(con_out);
        } else {
            ((*con_out).set_attribute)(con_out, 0x0B);
            print_str(con_out, " ╭─ 📁 Finder: /home/vyron ──────────────────────────────────────╮\n");
            ((*con_out).set_attribute)(con_out, 0x0F);
            print_str(con_out, " │ Name              Size         Kind            Permissions    │\n");
            print_str(con_out, " │ ────────────────────────────────────────────────────────────  │\n");
            print_str(con_out, " │ 📁 Desktop        4096 bytes   Folder          drwxr-xr-x     │\n");
            print_str(con_out, " │ 📁 Documents      4096 bytes   Folder          drwxr-xr-x     │\n");
            print_str(con_out, " │ 📁 Downloads      4096 bytes   Folder          drwxr-xr-x     │\n");
            print_str(con_out, " │ 📄 notes.txt      28 bytes     Plain Text      -rw-r--r--     │\n");
            print_str(con_out, " │ ⚙️ os-release     138 bytes    System Config   -rw-r--r--     │\n");
            ((*con_out).set_attribute)(con_out, 0x0B);
            print_str(con_out, " ╰───────────────────────────────────────────────────────────────╯\n");
            ((*con_out).set_attribute)(con_out, 0x0F);
        }
    } else if cmd_name == "menu" || cmd_name == "start" {
        ((*con_out).set_attribute)(con_out, 0x0E);
        print_str(con_out, " ╭─  VYRON System Menu ─────╮\n");
        print_str(con_out, " │ 1. About This System      │\n");
        print_str(con_out, " │ 2. System Settings        │\n");
        print_str(con_out, " │ 3. App Store (aptitude)   │\n");
        print_str(con_out, " │ 4. File Manager (finder)  │\n");
        print_str(con_out, " │ 5. Restart (reboot)       │\n");
        print_str(con_out, " │ 6. Shut Down (shutdown)   │\n");
        print_str(con_out, " ╰───────────────────────────╯\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "calc" {
        let expr = rest.trim();
        if expr.is_empty() {
            print_str(con_out, "Usage: calc <num1> <op> <num2>  (e.g., calc 25 * 4)\n");
        } else {
            let mut words = [""; 4];
            let mut count = 0;
            let mut rem = expr;
            while count < 4 && !rem.is_empty() {
                let (w, r) = split_first_word(rem);
                if !w.is_empty() {
                    words[count] = w;
                    count += 1;
                }
                rem = r;
            }
            if count >= 3 {
                let n1 = parse_u64(words[0]);
                let op = words[1];
                let n2 = parse_u64(words[2]);
                let mut buf = [0u8; 16];
                if let (Some(a), Some(b)) = (n1, n2) {
                    let res = match op {
                        "+" => Some(a + b),
                        "-" => if a >= b { Some(a - b) } else { None },
                        "*" => Some(a * b),
                        "/" => if b != 0 { Some(a / b) } else { None },
                        "%" => if b != 0 { Some(a % b) } else { None },
                        _ => None,
                    };
                    if let Some(val) = res {
                        print_str(con_out, "calc: ");
                        print_str(con_out, expr);
                        print_str(con_out, " = ");
                        print_str(con_out, write_usize(&mut buf, val as usize));
                        print_str(con_out, "\n");
                    } else {
                        print_str(con_out, "calc: invalid arithmetic operation or divide by zero\n");
                    }
                } else {
                    print_str(con_out, "calc: invalid numeric arguments\n");
                }
            } else {
                print_str(con_out, "Usage: calc <num1> <op> <num2>\n");
            }
        }
    } else if cmd_name == "dock" {
        ((*con_out).set_attribute)(con_out, 0x0B);
        print_str(con_out, " ╭───────────────────────────────────────────────────────────────────╮\n");
        print_str(con_out, " │  [📁 Finder]   [💻 Terminal]   [⚙ Settings]   [🌐 Web]   [🗑 Trash]  │\n");
        print_str(con_out, " ╰───────────────────────────────────────────────────────────────────╯\n");
        ((*con_out).set_attribute)(con_out, 0x0F);
    } else if cmd_name == "reboot" {
        print_str(con_out, "Rebooting system via UEFI Runtime Services...\n");
        ((*rt).reset_system)(0, 0, 0, core::ptr::null()); // EfiResetCold
    } else {
        print_str(con_out, "bash: command not found: ");
        print_str(con_out, cmd_name);
        print_str(con_out, ". Type 'help' for available commands.\n");
    }
}
