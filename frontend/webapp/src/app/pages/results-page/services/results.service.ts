import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { switchMap, tap } from 'rxjs';

@Injectable()
export class ResultsService {

  constructor(private http: HttpClient) { }

  getResults(requestId: string) {
    return this.http.get(`${environment.backendApiUrl}/results_url`, { params: { request_id: requestId } })
      .pipe(
        switchMap((res: any) => this.http.get(res.ResultUrl, { responseType: 'text' }))
      );
  }
}
