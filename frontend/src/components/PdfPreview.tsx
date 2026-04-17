import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import { Button } from "./ui/button";
import { useSettingsStore } from "../store/settings";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

interface Props {
  runId: string;
}

export function PdfPreview({ runId }: Props) {
  const backendUrl = useSettingsStore((s) => s.backendUrl).replace(/\/+$/, "");
  const pdfUrl = `${backendUrl}/api/v1/reports/${runId}.pdf`;
  const [numPages, setNumPages] = useState<number>(0);
  const [page, setPage] = useState(1);

  return (
    <div className="flex flex-col items-center gap-3 p-4">
      <Document
        file={pdfUrl}
        onLoadSuccess={({ numPages: n }) => setNumPages(n)}
        loading={
          <div className="text-sm text-muted-foreground">Loading PDF...</div>
        }
        error={
          <div className="text-sm text-destructive">Failed to load PDF</div>
        }
      >
        <Page
          pageNumber={page}
          width={540}
          renderAnnotationLayer={false}
          renderTextLayer={false}
        />
      </Document>

      {numPages > 0 && (
        <div className="flex items-center gap-3">
          <Button
            size="icon"
            variant="ghost"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs text-muted-foreground">
            {page} / {numPages}
          </span>
          <Button
            size="icon"
            variant="ghost"
            disabled={page >= numPages}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
            <Button size="sm" variant="outline">
              <Download className="h-3.5 w-3.5" /> Download
            </Button>
          </a>
        </div>
      )}
    </div>
  );
}
