from mmu import MMU
import random
from collections import deque

class RandMMU(MMU):
    def __init__(self, frames):
        # number of physical frames
        self.num_frames = frames
        # frame -> page_number (or None)
        self.frames = [None] * frames
        # page table: page_number -> {frame, valid, dirty, use}
        self.pt = {}
        # free frame queue
        self.free_frames = deque(range(frames))
        # stats
        self.disk_reads = 0
        self.disk_writes = 0
        self.page_faults = 0
        # debug flag
        self._debug = False

    def set_debug(self):
        self._debug = True

    def reset_debug(self):
        self._debug = False

    def _debug_print(self, *args):
        if self._debug:
            print(*args)

    def _allocate_free_or_victim(self):
        """Return (frame_index, victim_page_or_None). If a free frame exists, returns it with victim None."""
        if self.free_frames:
            frame = self.free_frames.popleft()
            return frame, None
        # choose random occupied frame
        idx = random.randrange(self.num_frames)
        return idx, self.frames[idx]

    def _load_page_into_frame(self, page_number, frame, is_write):
        """Mark page loaded into frame and update page table/stats."""
        # incoming disk read to bring page in
        self.disk_reads += 1
        self.frames[frame] = page_number
        pte = self.pt.get(page_number)
        if pte is None:
            pte = {'frame': frame, 'valid': True, 'dirty': bool(is_write), 'use': True}
            self.pt[page_number] = pte
        else:
            pte['frame'] = frame
            pte['valid'] = True
            pte['dirty'] = bool(is_write)
            pte['use'] = True

        self._debug_print(f"Loaded page {page_number} into frame {frame} (dirty={pte['dirty']})")

    def read_memory(self, page_number):
        # read -> no change to dirty on hit
        pte = self.pt.get(page_number)
        if pte and pte['valid']:
            # hit
            pte['use'] = True
            self._debug_print(f"READ HIT page {page_number} in frame {pte['frame']}")
            return
        # miss -> page fault
        self.page_faults += 1
        self._debug_print(f"READ MISS page {page_number}")
        frame, victim_page = self._allocate_free_or_victim()
        if victim_page is not None:
            # evict victim
            vpte = self.pt[victim_page]
            self._debug_print(f"  Evicting page {victim_page} from frame {frame} (dirty={vpte['dirty']})")
            if vpte['dirty']:
                self.disk_writes += 1
                self._debug_print(f"    Writing page {victim_page} to disk")
            vpte['valid'] = False
            vpte['frame'] = None
            vpte['use'] = False
        self._load_page_into_frame(page_number, frame, is_write=False)

    def write_memory(self, page_number):
        # write -> set dirty
        pte = self.pt.get(page_number)
        if pte and pte['valid']:
            # hit
            pte['dirty'] = True
            pte['use'] = True
            self._debug_print(f"WRITE HIT page {page_number} in frame {pte['frame']} (now dirty)")
            return
        # miss
        self.page_faults += 1
        self._debug_print(f"WRITE MISS page {page_number}")
        frame, victim_page = self._allocate_free_or_victim()
        if victim_page is not None:
            vpte = self.pt[victim_page]
            self._debug_print(f"  Evicting page {victim_page} from frame {frame} (dirty={vpte['dirty']})")
            if vpte['dirty']:
                self.disk_writes += 1
                self._debug_print(f"    Writing page {victim_page} to disk")
            vpte['valid'] = False
            vpte['frame'] = None
            vpte['use'] = False
        self._load_page_into_frame(page_number, frame, is_write=True)

    def get_total_disk_reads(self):
        return self.disk_reads

    def get_total_disk_writes(self):
        return self.disk_writes

    def get_total_page_faults(self):
        return self.page_faults
