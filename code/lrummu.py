from mmu import MMU
from collections import OrderedDict, deque

class LruMMU(MMU):
    def __init__(self, frames):
        # number of frames
        self.num_frames = frames
        # frame -> page (or None)
        self.frames = [None] * frames
        # page table: page -> {frame, valid, dirty, use}
        self.pt = {}
        # free frames
        self.free_frames = deque(range(frames))
        # keep LRU order as OrderedDict: key=page, value=frame. Least-recent at beginning.
        self.lru = OrderedDict()
        # stats
        self.disk_reads = 0
        self.disk_writes = 0
        self.page_faults = 0
        # debug
        self._debug = False

    def set_debug(self):
        self._debug = True

    def reset_debug(self):
        self._debug = False

    def _debug_print(self, *args):
        if self._debug:
            print(*args)

    def _evict_lru(self):
        # pop first item from OrderedDict (least recently used)
        if not self.lru:
            raise RuntimeError("LRU eviction requested but no pages present")
        victim_page, victim_frame = next(iter(self.lru.items()))
        # remove
        self.lru.pop(victim_page)
        return victim_frame, victim_page

    def _load_page(self, page_number, frame, is_write):
        # disk read to load page
        self.disk_reads += 1
        self.frames[frame] = page_number
        entry = self.pt.get(page_number)
        if entry is None:
            entry = {'frame': frame, 'valid': True, 'dirty': bool(is_write), 'use': True}
            self.pt[page_number] = entry
        else:
            entry.update({'frame': frame, 'valid': True, 'dirty': bool(is_write), 'use': True})
        # move to most-recent in lru
        if page_number in self.lru:
            self.lru.pop(page_number)
        self.lru[page_number] = frame
        self._debug_print(f"Loaded page {page_number} into frame {frame} (dirty={entry['dirty']})")

    def read_memory(self, page_number):
        entry = self.pt.get(page_number)
        if entry and entry['valid']:
            # hit: update LRU (move to end)
            entry['use'] = True
            if page_number in self.lru:
                self.lru.pop(page_number)
            self.lru[page_number] = entry['frame']
            self._debug_print(f"READ HIT page {page_number} in frame {entry['frame']}")
            return
        # miss
        self.page_faults += 1
        self._debug_print(f"READ MISS page {page_number}")
        if self.free_frames:
            frame = self.free_frames.popleft()
        else:
            frame, victim_page = self._evict_lru()
            ventry = self.pt[victim_page]
            self._debug_print(f"  Evicting page {victim_page} from frame {frame} (dirty={ventry['dirty']})")
            if ventry['dirty']:
                self.disk_writes += 1
                self._debug_print(f"    Writing page {victim_page} to disk")
            ventry['valid'] = False
            ventry['frame'] = None
            ventry['use'] = False
        self._load_page(page_number, frame, is_write=False)

    def write_memory(self, page_number):
        entry = self.pt.get(page_number)
        if entry and entry['valid']:
            # hit
            entry['dirty'] = True
            entry['use'] = True
            if page_number in self.lru:
                self.lru.pop(page_number)
            self.lru[page_number] = entry['frame']
            self._debug_print(f"WRITE HIT page {page_number} in frame {entry['frame']} (now dirty)")
            return
        # miss
        self.page_faults += 1
        self._debug_print(f"WRITE MISS page {page_number}")
        if self.free_frames:
            frame = self.free_frames.popleft()
        else:
            frame, victim_page = self._evict_lru()
            ventry = self.pt[victim_page]
            self._debug_print(f"  Evicting page {victim_page} from frame {frame} (dirty={ventry['dirty']})")
            if ventry['dirty']:
                self.disk_writes += 1
                self._debug_print(f"    Writing page {victim_page} to disk")
            ventry['valid'] = False
            ventry['frame'] = None
            ventry['use'] = False
        self._load_page(page_number, frame, is_write=True)

    def get_total_disk_reads(self):
        return self.disk_reads

    def get_total_disk_writes(self):
        return self.disk_writes

    def get_total_page_faults(self):
        return self.page_faults
