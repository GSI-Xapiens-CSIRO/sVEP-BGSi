import { Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatInputModule } from '@angular/material/input';
import { FormBuilder, FormControl, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { FileDropEvent, FileDropperComponent } from './file-dropper/file-dropper.component';
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
    FileDropperComponent,
    RouterLink,
    MatProgressSpinnerModule,
  ],
  providers: [JobsService],
  templateUrl: './submit-page.component.html',
  styleUrl: './submit-page.component.scss',
})
export class SubmitPageComponent {
  @ViewChild('dropper') private dropper!: FileDropperComponent;
  protected vcfFile: File | null = null;
  protected indexFile: File | null = null;
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
        this.dropper.reset();
      }
    });
  }

  filesDropped(event: FileDropEvent) {
    this.vcfFile = event.vcf;
    this.indexFile = event.index;
    this.valid = true;
    this.vcfFileInputControl.reset();
  }

  reset() {
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
    this.vcfFileInputControl.disable();

    if (this.vcfFile) {
      this.uploadStarted = true;
      this.sizeToUpload = this.vcfFile.size + this.indexFile!.size;
      let urlInfo: any = null;
      this.js.getUploadURLS(this.vcfFile!.name, this.indexFile!.name)
        .pipe(
          tap((u: any) => { urlInfo = u.urls }),
          switchMap(
            (result: any) => merge(
              this.js.uploadToURL(result.urls.vcf_url, this.vcfFile!),
              this.js.uploadToURL(result.urls.index_url, this.indexFile!),
            )
          ),
          tap((e) => this.handleProgress(e)),
          last()
        ).pipe(
          switchMap(() => {
            const bucket = urlInfo['vcf_url']['fields']['bucket'] ?? null;
            const key = urlInfo['vcf_url']['fields']['key'] ?? null;
            const s3URI = `s3://${bucket}/${key}`;

            console.log('uploaded', s3URI);
            return this.js.submitJob(s3URI);
          }),
          catchError(() => of(null))
        ).subscribe((response: any) => {
          if (!response) {
            this.sb.open('An error occured please check you input and try again later', 'Okay', { duration: 60000 });
            return;
          }
          this.results = response.RequestId ?? null;
          this.reset();
        });
    } else {
      this.js.submitJob(this.vcfFileInputControl.value)
        .pipe(catchError(() => of(null)))
        .subscribe((response: any) => {
          if (!response) {
            this.sb.open('An error occured please check you input and try again later', 'Okay', { duration: 60000 });
            return;
          }
          this.results = response.RequestId ?? null;
          this.reset();
        })
    }
  }
}

