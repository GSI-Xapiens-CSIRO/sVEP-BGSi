import { Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';


export interface FileDropEvent {
  vcf: File;
  index: File;
}
@Component({
  selector: 'app-file-dropper',
  standalone: true,
  imports: [
    CommonModule,
    CommonModule,
    MatSnackBarModule,
  ],
  templateUrl: './file-dropper.component.html',
  styleUrl: './file-dropper.component.scss'
})
export class FileDropperComponent {
  @Input() disabled = false;
  @Output() dropped = new EventEmitter<FileDropEvent>();
  @ViewChild('dropzone') private dropzone!: ElementRef;

  protected vcfFile: File | null = null;
  protected indexFile: File | null = null;

  constructor(
    private sb: MatSnackBar,
  ) { }

  highlight(e: Event) {
    this.dropzone.nativeElement.classList.add('svep-dropper-active');
  }

  unhighlight(e: Event) {
    this.dropzone.nativeElement.classList.remove('svep-dropper-active');
  }

  handleDrop(e: DragEvent) {
    const files: FileList = e.dataTransfer?.files ?? new FileList();
    this.handleFiles(files);
  }

  handlePick(e: Event) {
    const files = (e.target as HTMLInputElement).files ?? new FileList();
    this.handleFiles(files);
  }

  handleFiles(files: FileList) {
    // validations >>
    if (files.length > 2) {
      this.sb.open('Must be two files at most, vcf and index.', 'Okay', { duration: 60000 });
      return;
    }
    for (let index = 0; index < files.length; index++) {
      const file: File = files.item(index)!;
      if (!(file.name.toLowerCase().endsWith('.vcf.gz') || file.name.toLowerCase().endsWith('.tbi') || file.name.toLowerCase().endsWith('.csi'))) {
        this.sb.open('Must be format did not match vcf or index.', 'Okay', { duration: 60000 });
        return;
      }
    }
    for (let index = 0; index < files.length; index++) {
      const file: File = files.item(index)!;
      if (file.name.toLowerCase().endsWith('.vcf.gz')) {
        this.vcfFile = file;
      }
      if (file.name.toLowerCase().endsWith('.tbi') || file.name.toLowerCase().endsWith('.csi')) {
        this.indexFile = file;
      }
    }
    if (this.vcfFile && this.indexFile) {
      const correct = this.vcfFile.name === this.indexFile.name.replace(/\.(tbi|csi)$/i, '');
      if (!correct) {
        this.sb.open('VCF and index file names must match.', 'Okay', { duration: 60000 });
        this.reset();
        return;
      }
    }
    // validations <<
    if (this.vcfFile && this.indexFile) {
      this.dropped.emit({ vcf: this.vcfFile, index: this.indexFile });
    }
  }

  preventDefaults(e: Event) {
    e.preventDefault();
    e.stopPropagation();
  }

  reset() {
    this.vcfFile = null;
    this.indexFile = null;
  }
}
