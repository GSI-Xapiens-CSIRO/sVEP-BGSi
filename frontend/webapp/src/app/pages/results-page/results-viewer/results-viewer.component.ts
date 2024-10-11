import { AfterViewInit, Component, Input, OnChanges, SimpleChanges, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';

@Component({
  selector: 'app-results-viewer',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
  ],
  templateUrl: './results-viewer.component.html',
  styleUrl: './results-viewer.component.scss'
})
export class ResultsViewerComponent implements OnChanges, AfterViewInit {
  @Input({ required: true }) results!: any;
  @ViewChild('paginator') paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  protected columns: string[] = ['Rank', '.', 'Region', 'Alt Allele', 'Consequence', 'Gene Name', 'Gene ID', 'Feature', 'Transcript ID & Version', 'Transcript Biotype', 'Exon Number', 'Amino Acid Change', 'Codon Change', 'Strand', 'Transcript Support Level'];
  protected data = new MatTableDataSource<any>([]);;

  ngAfterViewInit(): void {
    this.data.paginator = this.paginator;
    this.data.sort = this.sort;
  }

  ngOnChanges(changes: SimpleChanges): void {
    const results: string = changes['results'].currentValue.body;

    if (results) {
      const lines = results.split('\n');
      this.data = new MatTableDataSource<any>(
        lines
          .filter((l) => l.length > 0)
          .map(l => {
            const row: any = {};
            l.split('\t').forEach((v, i) => {
              row[this.columns[i]] = v;
            });
            return row;
          })
      );
      this.data.sort = this.sort;
    }
  }
}
