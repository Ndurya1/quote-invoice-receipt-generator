import DocumentCanvas from '../../documents/components/DocumentCanvas.jsx';

export default function QuotationCanvas({ quotation, client, businessProfile }) {
  return <DocumentCanvas document={quotation} client={client} businessProfile={businessProfile} type="quotation" />;
}
