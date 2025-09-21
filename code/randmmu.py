"""
Implementation of the Random Page Replacement Algorithm. 
Written by Hung a1884747
"""


from mmu import MMU
import random


class RandMMU(MMU):


    def __init__(self, frames):
        self.frames = frames
        self.page_table = {}  # page_number -> {'frame': frame_number, 'modified': bool}
        self.free_frames = list(range(frames))  # list of free frames
        # stats
        self.total_disk_reads = 0
        self.total_disk_writes = 0
        self.total_page_faults = 0
        # debug
        self.verbose = False
        

    def _evict_random_page(self):
        # randomly choose victim page to evict
        victim_page = random.choice(list(self.page_table.keys()))
        victim_info = self.page_table[victim_page]
        frame = victim_info['frame']
        if self.verbose:
            print(f"Randomly selected page {victim_page} in frame {frame} for eviction")
        
        # stat update
        if victim_info['modified']:
            self.total_disk_writes += 1
            if self.verbose:
                print(f"Writing modified page {victim_page} to disk")
        
        # remove victim from page table, but still exists on disk
        del self.page_table[victim_page]
        if self.verbose:
            print(f"Evicted page {victim_page} from frame {frame}")
        return frame


    def read_memory(self, page_number):
        if self.verbose:
            print(f"Reading page {page_number}")
        
        # check for hit
        if page_number in self.page_table:
            if self.verbose:
                frame = self.page_table[page_number]
                print(f"Page {page_number} found in frame {frame}")
            return
        
        # miss/page-fault, therefore must be read from disk
        self.total_disk_reads += 1
        self.total_page_faults += 1
        if self.verbose:
            print(f"Page fault for page {page_number}")
        
        # find empty frame
        if self.free_frames:
            frame = self.free_frames.pop(0)
            if self.verbose:
                print(f"Using free frame {frame}")
        else:
            # evict with random replacement policy
            frame = self._evict_random_page()
            
        # load page into frame
        self.page_table[page_number] = {'frame': frame, 'modified': False}
        if self.verbose:
            print(f"Loaded page {page_number} into frame {frame}")
    

    def write_memory(self, page_number):
        if self.verbose:
            print(f"Writing to page {page_number}")
            
        # check for hit
        if page_number in self.page_table:
            self.page_table[page_number]['modified'] = True
            if self.verbose:
                frame = self.page_table[page_number]['frame']
                print(f"Page {page_number} in frame {frame} marked as modified")
            return
        
        # miss/page-fault, therefore must be read from disk
        self.total_page_faults += 1
        self.total_disk_reads += 1

        if self.verbose:
            print(f"Page fault for page {page_number} (write)")
        
        # find empty frame
        if self.free_frames:
            frame = self.free_frames.pop(0)
            if self.verbose:
                print(f"Using free frame {frame}")
        else:
            # evict with random replacement policy
            frame = self._evict_random_page()
            
        # load page into frame
        self.page_table[page_number] = {'frame': frame, 'modified': True}
        if self.verbose:
            print(f"Loaded page {page_number} into frame {frame} and marked as modified")
    

    # debug methods
    def set_debug(self):
        self.verbose = True
    def reset_debug(self):
        self.verbose = False


    # stats for memsim.py
    def get_total_disk_reads(self):
        return self.total_disk_reads
    def get_total_disk_writes(self):
        return self.total_disk_writes
    def get_total_page_faults(self):
        return self.total_page_faults