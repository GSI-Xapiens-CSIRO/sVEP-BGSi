import { HttpClient, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../../environments/environment';

@Injectable()
export class JobsService {
  constructor(private http: HttpClient) {}

  getUploadURLS(vcf: string, index: string) {
    return this.http.get(`${environment.frontendApiUrl}/signed_url`, {
      params: {
        vcf,
        index,
      },
    });
  }

  uploadToURL(url: any, file: File) {
    const formData = new FormData();
    for (const key in url.fields) {
      formData.append(key, url.fields[key]);
    }
    formData.append('file', file);
    const request = new HttpRequest('POST', url.url, formData, {
      reportProgress: true,
    });
    return this.http.request(request);
  }

  submitJob(location: string) {
    return this.http.post(`${environment.backendApiUrl}/submit`, { location });
  }
}
