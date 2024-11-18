import { Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatInputModule } from '@angular/material/input';
import { FormBuilder, FormControl, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { FileSelectEvent, ProjectsListComponent } from './projects-list/projects-list.component'
import { MatFormFieldModule } from '@angular/material/form-field';
import { JobsService } from './services/jobs.service';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { catchError, last, merge, of, switchMap, tap } from 'rxjs';
import { RouterLink } from '@angular/router';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-submit-page',
  standalone: true,
  imports: [
    CommonModule,
    MatSnackBarModule,
    MatButtonModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    FormsModule,
    ReactiveFormsModule,
    ProjectsListComponent,
    RouterLink,
    MatProgressSpinnerModule,
  ],
  providers: [JobsService],
  templateUrl: './submit-page.component.html',
  styleUrl: './submit-page.component.scss',
})
export class SubmitPageComponent {
  @ViewChild('projects') private projects!: ProjectsListComponent;
  protected vcfFile: string | null = null;
  protected indexFile: string | null = null;
  protected valid = false;
  protected submissionStarted = false;
  protected vcfFileInputControl: FormControl;
  protected uploadStarted = false;
  protected sizeToUpload = 0;
  protected uploadedAmount = 0;
  protected results = null;

  constructor(
    private fb: FormBuilder,
    private js: JobsService,
    private sb: MatSnackBar,
  ) {
    this.vcfFileInputControl = this.fb.control('', [Validators.required, Validators.minLength(6), Validators.pattern(/^s3:\/\/([^\/]+)\/(.+)\.vcf\.gz$/i)]);
    this.vcfFileInputControl.valueChanges.subscribe((value) => {
      if (value) {
        this.vcfFile = null;
        this.indexFile = null;
      }
    });
  }

  filesSelected(event: FileSelectEvent) {
    console.log(event.vcf);
    this.vcfFile = event.vcf;
    this.indexFile = event.index;
    this.valid = true;
    this.vcfFileInputControl.reset();
  }

  reset() {
    this.projects.list()
    this.submissionStarted = false;
    this.uploadStarted = false;
    this.valid = false;
    this.vcfFileInputControl.reset()
  }

  handleProgress(event: HttpEvent<any>) {
    switch (event.type) {
      case HttpEventType.UploadProgress:
        this.uploadedAmount += event.loaded;
        break;
      default:
        break;
    }
  }

  submit() {
    this.submissionStarted = true;

    if (this.vcfFile) {
      const s3URI = `s3://sbeacon-backend-dataportal-20241107003128459300000004/${this.vcfFile}`;
      
      this.js.submitJob(s3URI)
        .pipe(
          catchError(() => of(null))
        )
        .subscribe((response: any) => {
          if (!response) {
            this.sb.open('An error occurred please check your input and try again later', 'Okay', { duration: 60000 });
            return;
          }
          this.results = response.RequestId ?? null;
          this.reset();
        });
    } else {
      this.sb.open('No file selected', 'Okay', { duration: 5000 });
      this.submissionStarted = false;
    }
  }
}

