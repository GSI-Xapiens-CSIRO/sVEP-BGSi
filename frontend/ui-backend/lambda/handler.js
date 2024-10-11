import { S3Client } from '@aws-sdk/client-s3';
import { createPresignedPost } from '@aws-sdk/s3-presigned-post';
import { ProxyRouter, build_response } from './utils/router.js';
import _ from 'lodash';


const BUCKET_NAME = process.env.BUCKET_NAME;
const client = new S3Client();


const get_s3_signed_url_to_post_data = async (request_id, vcf_name, index_name) => {
  const vcf = `uploads/${request_id}_${vcf_name}`;
  const index = `uploads/${request_id}_${index_name}`;
  const vcf_url = await createPresignedPost(
    client,
    { Bucket: BUCKET_NAME, Key: vcf },
    {
      Conditions: [
        ["content-length-range", 0, 200000000]
      ]
    });
  const index_url = await createPresignedPost(client,
    { Bucket: BUCKET_NAME, Key: index },
    {
      Conditions: [
        ["content-length-range", 0, 200000000]
      ]
    });
  return { vcf_url, index_url };
}

export const lambda_handler = (_event, _context, _callback) => {
  const router = new ProxyRouter(_event, _context, _callback);
  _context.callbackWaitsForEmptyEventLoop = false;

  router.route(
    'GET',
    '/signed_url',
    async (event, context, callback) => {
      try {
        const vcf = _.get(event, 'queryStringParameters.vcf');
        const index = _.get(event, 'queryStringParameters.index');
        const request_id = _.get(event, 'requestContext.requestId');

        if (!vcf || !index) {
          throw Error('VCF and Index both are required');
        }

        const urls = await get_s3_signed_url_to_post_data(request_id, vcf, index);
        
        callback(null, build_response(200, { success: true, urls }));
      } catch (error) {
        callback(null, build_response(400, { success: false, error: error.message }));
      }
    }
  )
};
