import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { FormBuilder, FormControl, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { BehaviorSubject, catchError, filter, of } from 'rxjs';
import { ResultsViewerComponent } from './results-viewer/results-viewer.component';
import { ResultsService } from './services/results.service';
import { FullPageLoaderService } from '../../services/full-page-loader.service';

@Component({
  selector: 'app-results-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    MatButtonModule,
    FormsModule,
    MatFormFieldModule,
    ReactiveFormsModule,
    MatInputModule,
    ResultsViewerComponent,
  ],
  providers: [ResultsService],
  templateUrl: './results-page.component.html',
  styleUrl: './results-page.component.scss'
})
export class ResultsPageComponent implements OnInit {
  protected requestIdFormControl: FormControl;
  protected results: any = null;
  private url = new BehaviorSubject<string>('');

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private rs: ResultsService,
    private ls: FullPageLoaderService,
  ) {
    this.requestIdFormControl = this.fb.control('', [Validators.required]);
    this.route.paramMap.subscribe((r: any) => {
      this.requestIdFormControl.patchValue(r.params.url ?? '');
      this.url.next(r.params.url ?? '');
    });
  }

  ngOnInit(): void {
    this.url.pipe(filter((u) => !!u)).subscribe(url => {
      this.load();
    })
  }

  load() {
    this.ls.start();
    this.rs.getResults(this.requestIdFormControl.value).pipe(catchError(() => of(null))).subscribe(data => {
      if (data) {
        this.results = data;
      }
      this.ls.end()
    });
  }
}
