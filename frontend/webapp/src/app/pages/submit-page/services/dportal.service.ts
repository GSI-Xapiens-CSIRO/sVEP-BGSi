import { Injectable } from '@angular/core';
import { API, Auth } from 'aws-amplify';
import { from } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class DportalService {
  constructor() {}

  // data portal user actions
  getMyProjects() {
    console.log('get my projects');
    return from(
      API.get(environment.api_endpoint_sbeacon.name, 
        'dportal/projects', 
        {}),
    );
  }

  getMyProjectFile(project: string, prefix: string) {
    console.log('get my project file');
    return from(
      API.get(
        environment.api_endpoint_sbeacon.name,
        `dportal/projects/${project}/file`,
        {
          queryStringParameters: { prefix },
        },
      ),
    );
  }
}