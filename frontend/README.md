# Setup

## Deployment

In order to deploy sVEP UI, please ensure you have Node.js installed with version > v18.13, as well as npm.

This project was generated with [Angular CLI](https://github.com/angular/angular-cli) version 17.0.1. After cloning the repository please run following commands;

```
npm install -g pnpm

cd webapp

pnpm install
```

These commands will install pnpm, navigate to the web application directory, and install required node modules, respectively.

Once dependencies are installed, navigate to terraform-aws and run;

```
terraform apply
```

Deployment requires the API URL for uploading files. Accept the deployment and, when complete, copy the template environment file `webapp/src/environments/example.environment.ts` to `webapp/src/environemtns/environment.ts` and replace the placeholder urls with the urls provided by terraform's output.

Now deploy again to make the changes take effect.