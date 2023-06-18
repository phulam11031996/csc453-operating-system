import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Scanner;

public class memSim {
    private static final int PAGE_SIZE = 256;
    private static final int PAGE_TABLE_SIZE = 256;
    private static final int TLB_SIZE = 5;
    private static int FRAME_SIZE = 10;

    public class TLBEntry {
        private int pageNumber;
        private int frameNumber;

        public TLBEntry(int pageNumber, int frameNumber) {
            this.pageNumber = pageNumber;
            this.frameNumber = frameNumber;
        }

        public int getPageNumber() {
            return pageNumber;
        }

        public int getFrameNumber() {
            return frameNumber;
        }

        public void setFrameNumber(int frameNumber) {
            this.frameNumber = frameNumber;
        }

        public void setPageNumber(int pageNumber) {
            this.pageNumber = pageNumber;
        }
    }

    public class TLB {
        private List<TLBEntry> entries = new ArrayList<>();

        public int addEntry(TLBEntry entry) {
            int previousPage = -1;

            for (int i = 0; i < entries.size(); i++) {
                TLBEntry currentEntry = entries.get(i);

                if (currentEntry.getPageNumber() == entry.getPageNumber()) {
                    currentEntry.setFrameNumber(entry.getFrameNumber());
                    return previousPage;
                }

                if (currentEntry.getFrameNumber() == entry.getFrameNumber()) {
                    previousPage = currentEntry.getPageNumber();
                    currentEntry.setPageNumber(entry.getPageNumber());
                    return previousPage;
                }
            }

            if (entries.size() == TLB_SIZE) {
                previousPage = entries.get(0).getFrameNumber();
                entries.remove(0);
            }

            entries.add(entry);
            return previousPage;
        }

        public List<TLBEntry> getEntries() {
            return new ArrayList<>(entries);
        }
    }

    public class PageTableEntry {
        private boolean valid;
        private int frameNumber;

        public PageTableEntry() {
            valid = false;
            frameNumber = -1;
        }

        public boolean isValid() {
            return valid;
        }

        public void setValid(boolean valid) {
            this.valid = valid;
        }

        public int getFrameNumber() {
            return frameNumber;
        }

        public void setFrameNumber(int frameNumber) {
            this.frameNumber = frameNumber;
        }
    }

    public class PageTable {
        private PageTableEntry[] entries;

        public PageTable() {
            entries = new PageTableEntry[PAGE_TABLE_SIZE];
            initializeEntries();
        }

        private void initializeEntries() {
            for (int i = 0; i < PAGE_TABLE_SIZE; i++) {
                entries[i] = new PageTableEntry();
            }
        }

        public PageTableEntry getEntry(int pageNumber) {
            if (isValidPageNumber(pageNumber)) {
                return entries[pageNumber];
            }
            return null;
        }

        public void updateEntry(int pageNumber, boolean valid, int frameNumber) {
            if (isValidPageNumber(pageNumber)) {
                PageTableEntry entry = entries[pageNumber];
                entry.setValid(valid);
                entry.setFrameNumber(frameNumber);
            }
        }

        public void updateValid(int pageNumber, boolean valid) {
            if (isValidPageNumber(pageNumber)) {
                entries[pageNumber].setValid(valid);
            }
        }

        private boolean isValidPageNumber(int pageNumber) {
            return pageNumber >= 0 && pageNumber < PAGE_TABLE_SIZE;
        }
    }

    public class BackingStore {
        private static final String BACKING_STORE_FILE = "BACKING_STORE.bin";
        private static final int BLOCK_SIZE = PAGE_SIZE;

        private byte[] data;

        public BackingStore() {
            try {
                Path filePath = Paths.get(BACKING_STORE_FILE);
                data = Files.readAllBytes(filePath);
            } catch (IOException e) {
                e.printStackTrace();
                data = new byte[0]; // Initialize with an empty array on failure
            }
        }

        public byte[] getPageData(int pageNumber) {
            int startIndex = pageNumber * BLOCK_SIZE;
            int endIndex = startIndex + BLOCK_SIZE;
            if (isValidRange(startIndex, endIndex)) {
                return Arrays.copyOfRange(data, startIndex, endIndex);
            }
            return null;
        }

        private boolean isValidRange(int startIndex, int endIndex) {
            return startIndex >= 0 && endIndex <= data.length;
        }
    }

    abstract class PhysicalMemory {
        protected int numberOfFrames;
        protected LinkedList<byte[]> frames;

        public PhysicalMemory(int numberOfFrames) {
            this.numberOfFrames = numberOfFrames;
            this.frames = new LinkedList<>();
        }

        public byte[] readFrame(int frameNumber) {
            return frames.get(frameNumber);
        }

        public void writeFrame(int frameNumber, byte[] data) {
            frames.set(frameNumber, data);
        }

        public abstract int replacePage(int pageNumber, byte[] data);
    }

    class FIFO extends PhysicalMemory {
        private int nextFrameIndex;

        public FIFO(int numberOfFrames) {
            super(numberOfFrames);
            this.nextFrameIndex = 0;
        }

        @Override
        public int replacePage(int pageNumber, byte[] data) {
            int replacedFrame = nextFrameIndex;
            if (frames.size() < numberOfFrames) {
                frames.addLast(data);
            } else {
                frames.set(nextFrameIndex, data);
            }
            nextFrameIndex = (nextFrameIndex + 1) % numberOfFrames;
            return replacedFrame;
        }
    }

    class LRU extends PhysicalMemory {
        private LinkedList<Integer> pageOrder;

        public LRU(int numberOfFrames) {
            super(numberOfFrames);
            pageOrder = new LinkedList<>();
        }

        @Override
        public int replacePage(int pageNumber, byte[] data) {
            int replacedFrame;
            if (super.frames.size() < numberOfFrames) {
                replacedFrame = super.frames.size();
                frames.addLast(data);
            } else {
                replacedFrame = pageOrder.removeFirst();
                frames.set(replacedFrame, data);
            }
            pageOrder.addLast(replacedFrame);
            return replacedFrame;
        }

        @Override
        public void writeFrame(int frameNumber, byte[] data) {
            super.writeFrame(frameNumber, data);
            pageOrder.remove((Integer) frameNumber);
            pageOrder.addLast(frameNumber);
        }

        @Override
        public byte[] readFrame(int frameNumber) {
            pageOrder.remove((Integer) frameNumber);
            pageOrder.addLast(frameNumber);
            return super.readFrame(frameNumber);
        }
    }

    class OPT extends PhysicalMemory {
        private List<Integer> pageReferences;
        private List<Integer> pages;
        private int startingIndex;

        public OPT(int numberOfFrames, List<Integer> pageReferences) {
            super(numberOfFrames);
            this.pageReferences = pageReferences;
            this.pages = new ArrayList<>(numberOfFrames);
            this.startingIndex = numberOfFrames;
        }

        @Override
        public int replacePage(int pageNumber, byte[] data) {
            if (frames.size() < numberOfFrames) {
                frames.add(data);
                pages.add(pageNumber);
                return frames.size() - 1;
            }

            int replacedFrame = findPageToReplace();

            pages.set(replacedFrame, pageNumber);
            frames.set(replacedFrame, data);
            return replacedFrame;
        }

        private int findPageToReplace() {
            int pick = 0;
            int currentMax = 0;

            for (int i = 0; i < pages.size(); i++) {
                int position = findNextPageIndex(pages.get(i), startingIndex);
                if (position > currentMax) {
                    pick = i;
                    currentMax = position;
                }
            }

            return pick;
        }

        private int findNextPageIndex(int pageNumber, int startIndex) {
            for (int i = startIndex; i < pageReferences.size(); i++) {
                if (pageReferences.get(i) / PAGE_SIZE == pageNumber) {
                    return i;
                }
            }
            return this.pageReferences.size() - 1;
        }
    }

    public static List<Integer> getPageReferences(String fileName) {
        List<Integer> pageReferences = new ArrayList<>();

        try {
            File file = new File(fileName);
            Scanner scanner = new Scanner(file);

            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                int pageReference = Integer.parseInt(line.trim());
                pageReferences.add(pageReference);
            }

            scanner.close();
        } catch (IOException e) {
            e.printStackTrace();
        }

        return pageReferences;
    }

    public static void main(String[] args) {

        if (args.length < 3) {
            System.out.println("Usage: memSim <reference-sequence-file.txt><FRAMES><PRA>");
            return;
        }
        String referenceFile = args[0];
        FRAME_SIZE = Integer.parseInt(args[1]);
        String pageReplacementAlgorithm = args[2];

        // Perform memory accesses
        List<Integer> pageReferences = getPageReferences(referenceFile);

        // Create instances of the necessary components
        memSim memSimulator = new memSim();
        TLB tlb = memSimulator.new TLB();
        PageTable pageTable = memSimulator.new PageTable();
        BackingStore backingStore = memSimulator.new BackingStore();
        PhysicalMemory physicalMemory = memSimulator.new FIFO(FRAME_SIZE);

        switch (pageReplacementAlgorithm) {
            case "FIFO":
                physicalMemory = memSimulator.new FIFO(FRAME_SIZE);
                break;
            case "LRU":
                physicalMemory = memSimulator.new LRU(FRAME_SIZE);
                break;
            case "OPT":
                physicalMemory = memSimulator.new OPT(FRAME_SIZE, pageReferences);
                break;
            default:
                System.out.println("Invalid algorithm");
                break;
        }

        int tlbMisses = 0;
        int tlbHits = 0;
        int pageFaults = 0;

        for (Integer pageReference : pageReferences) {
            // Check TLB for the page
            int pageNumber = pageReference / PAGE_SIZE;
            int offset = pageReference % PAGE_SIZE;
            TLBEntry tlbEntry = null;
            for (TLBEntry entry : tlb.getEntries()) {
                if (entry.getPageNumber() == pageNumber) {
                    tlbEntry = entry;
                    break;
                }
            }

            byte[] pageData = null;
            int frameNumber = 0;

            if (tlbEntry != null) {
                // TLB hit, retrieve the frame number
                tlbHits++;
                frameNumber = tlbEntry.getFrameNumber();
                pageData = physicalMemory.readFrame(frameNumber);
                // Process the frame data as needed
            } else {
                // TLB miss, check page table
                tlbMisses++;
                PageTableEntry pageTableEntry = pageTable.getEntry(pageNumber);
                if (pageTableEntry.isValid()) {
                    // Page table hit, retrieve the frame number
                    frameNumber = pageTableEntry.getFrameNumber();
                    pageData = physicalMemory.readFrame(frameNumber);
                    // Process the frame data as needed

                    // Update TLB
                    TLBEntry newTLBEntry = memSimulator.new TLBEntry(pageNumber, frameNumber);
                    tlb.addEntry(newTLBEntry);
                } else {
                    pageFaults++;
                    // Page fault, load page from backing store
                    pageData = backingStore.getPageData(pageNumber);
                    // Process the page data as needed

                    // Replace a page in physical memory using the chosen page replacement algorithm
                    frameNumber = physicalMemory.replacePage(pageNumber, pageData);

                    // Update TLB
                    TLBEntry newTLBEntry = memSimulator.new TLBEntry(pageNumber, frameNumber);
                    int previousPage = tlb.addEntry(newTLBEntry);

                    // Update page table
                    if (previousPage != -1) {
                        pageTable.updateValid(previousPage, false);
                    }

                    pageTable.updateEntry(pageNumber, true, frameNumber);
                }
            }
            String pageDataHex = "";
            for (byte b : pageData) {
                pageDataHex += String.format("%02X", b);
            }
            System.out.printf("%d, %d, %d, %s\n", pageReference, pageData[offset], frameNumber, pageDataHex);
        }

        int requests = pageReferences.size();
        double pageFaultRate = (double) pageFaults / requests;
        double tlbHitRate = (double) tlbHits / requests;

        System.out.println("Number of Translated Addresses = " + requests);
        System.out.println("Page Faults = " + pageFaults);
        System.out.printf("Page Fault Rate = %.3f%n", pageFaultRate);
        System.out.println("TLB Hits = " + tlbHits);
        System.out.println("TLB Misses = " + tlbMisses);
        System.out.printf("TLB Hit Rate = %.3f%n", tlbHitRate);
    }
}
