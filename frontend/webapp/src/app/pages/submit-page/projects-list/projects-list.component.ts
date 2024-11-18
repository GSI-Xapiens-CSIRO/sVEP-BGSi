import { Component, Output, EventEmitter } from '@angular/core';
import { DportalService } from '../services/dportal.service'
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, of, tap } from 'rxjs';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatRadioModule } from '@angular/material/radio';

interface ProjectFile {
  filename: string;
  hasindex: boolean;
}

interface Project {
  name: string;
  description: string;
  files: ProjectFile[];
  indexed: boolean;
}

export interface FileSelectEvent {
  vcf: string;
  index: string;
}

@Component({
  selector: 'app-projects-list',
  standalone: true,
  imports: [
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatRadioModule,
  ],
  templateUrl: './projects-list.component.html',
  styleUrl: './projects-list.component.scss',
})
export class ProjectsListComponent {
  @Output() filesSelected = new EventEmitter<FileSelectEvent>();
  loading = true;
  dataSource = new MatTableDataSource<Project>();
  displayedColumns: string[] = [
    'name',
    'description',
    'files',
    // 'actions',
  ];
  assignTo: string | null = null;
  viewUsers: string | null = null;
  vcfFile: string | null = null;
  indexFile: string | null = null;

  constructor(
    private dps: DportalService,
    private sb: MatSnackBar,
    private dg: MatDialog,
  ) {
    this.list();
  }

  list() {
    this.dps
      .getMyProjects()
      .pipe(
        catchError((error) => {
          console.error('Error fetching projects:', error);  // Log the error
          return of(null);  // Return null to continue the stream
        })
      )
      .subscribe((data: any[]) => {
        if (!data) {
          this.sb.open('API request failed', 'Okay', { duration: 60000 });
          this.dataSource.data = [];
        } else {
          this.dataSource.data = data.map((project) => {
            const vcfFiles = project.files.filter((file: string) => file.endsWith('.vcf.gz'));
            const filesWithStatus = vcfFiles.map((file: string) => {
              const prefix = file.slice(0, -7);
              const hasIndex = project.files.includes(`${prefix}.vcf.gz.tbi`);
              return {
                filename: file,
                disabled: !hasIndex,
              };
            });
  
            return {
              name: project.name,
              description: project.description,
              files: filesWithStatus,
              indexed: false,
            };
          });
        }
        this.loading = false;
      });
  }

  isFileSelected(fileName: string): boolean {
    return this.vcfFile === fileName;
  }

  onFileSelect(fileName: string) {
    const fileEvent: FileSelectEvent = {
      vcf: fileName,
      index: `${fileName}.tbi`
    }
    this.filesSelected.emit(fileEvent);
  }

  getSelectedFile() {
    return this.vcfFile;
  }
}