from mmu import MMU
from collections import deque

class ClockMMU(MMU):
    def __init__(self, frames):
        self.num_frames = frames
        self.frames = [None] * frames  # index -> page
        self.pt = {}  # page -> {frame, valid, dirty, use}
        self.free_frames = deque(range(frames))
        # clock hand points to next candidate index
        self.clock_hand = 0
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

    def _find_victim_clock(self):
        """
        Classic Clock / Second-Chance algorithm (no special clean-page preference).
        Scan frames circularly starting at clock_hand:
          - if page.use == 0 -> choose it (victim)
          - else set page.use = 0 and advance
        Repeat until a victim is found.
        """
        n = self.num_frames
        # This loop is guaranteed to terminate because each iteration either picks a victim
        # or clears a use bit; after at most n clears we will find a use==0.
        while True:
            idx = self.clock_hand
            p = self.frames[idx]
            # If (unexpectedly) the slot is free, return it immediately
            if p is None:
                self.clock_hand = (idx + 1) % n
                return idx, p
            pte = self.pt[p]
            if not pte['use']:
                # choose this victim; advance hand to next slot for future
                self.clock_hand = (idx + 1) % n
                return idx, p
            # give second chance: clear use bit and advance hand
            pte['use'] = False
            self.clock_hand = (idx + 1) % n
            # continue loop

    def _load_page(self, page_number, frame, is_write):
        # disk read to load page
        self.disk_reads += 1
        # put page into frame
        self.frames[frame] = page_number
        entry = self.pt.get(page_number)
        if entry is None:
            entry = {'frame': frame, 'valid': True, 'dirty': bool(is_write), 'use': True}
            self.pt[page_number] = entry
        else:
            entry.update({'frame': frame, 'valid': True, 'dirty': bool(is_write), 'use': True})
        self._debug_print(f"Loaded page {page_number} into frame {frame} (dirty={entry['dirty']})")

    def read_memory(self, page_number):
        entry = self.pt.get(page_number)
        if entry and entry['valid']:
            entry['use'] = True
            self._debug_print(f"READ HIT page {page_number} in frame {entry['frame']}")
            return
        # page fault
        self.page_faults += 1
        self._debug_print(f"READ MISS page {page_number}")
        if self.free_frames:
            frame = self.free_frames.popleft()
        else:
            frame, victim_page = self._find_victim_clock()
            ventry = self.pt[victim_page]
            self._debug_print(f"  Removing page {victim_page} from frame {frame} (dirty={ventry['dirty']}, use={ventry['use']})")
            if ventry['dirty']:
                self.disk_writes += 1
                self._debug_print(f"    Writing page {victim_page} to disk")
            # mark victim invalid
            ventry['valid'] = False
            ventry['frame'] = None
            ventry['use'] = False
            # (optional) clear frame slot to avoid stale mapping until load
            self.frames[frame] = None
        self._load_page(page_number, frame, is_write=False)

    def write_memory(self, page_number):
        entry = self.pt.get(page_number)
        if entry and entry['valid']:
            entry['use'] = True
            entry['dirty'] = True
            self._debug_print(f"WRITE HIT page {page_number} in frame {entry['frame']} (now dirty)")
            return
        # page fault
        self.page_faults += 1
        self._debug_print(f"WRITE MISS page {page_number}")
        if self.free_frames:
            frame = self.free_frames.popleft()
        else:
            frame, victim_page = self._find_victim_clock()
            ventry = self.pt[victim_page]
            self._debug_print(f"  Removing page {victim_page} from frame {frame} (dirty={ventry['dirty']}, use={ventry['use']})")
            if ventry['dirty']:
                self.disk_writes += 1
                self._debug_print(f"    Writing page {victim_page} to disk")
            ventry['valid'] = False
            ventry['frame'] = None
            ventry['use'] = False
            self.frames[frame] = None
        self._load_page(page_number, frame, is_write=True)

    def get_total_disk_reads(self):
        return self.disk_reads

    def get_total_disk_writes(self):
        return self.disk_writes

    def get_total_page_faults(self):
        return self.page_faults
