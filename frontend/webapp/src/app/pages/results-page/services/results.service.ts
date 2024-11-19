import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { Auth } from 'aws-amplify'
import { from, Observable, switchMap } from 'rxjs';

@Injectable()
export class ResultsService {

  constructor(private http: HttpClient) { }

  getResults(requestId: string): Observable<any> {
    return from(Auth.currentCredentials()).pipe(
      switchMap((credentials) => {
        const userId = credentials.identityId;
        return this.http.get(`${environment.backendApiUrl}/results_url`, { params: { request_id: requestId, user_id: userId } })
          .pipe(
            switchMap((res: any) => this.http.get(res.ResultUrl, { responseType: 'text' }))
          );
      })
    );
  }
}
