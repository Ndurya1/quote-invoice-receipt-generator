import { isAuthPreviewEnabled } from '../../auth/authPreview.js';

export default function DeveloperPreviewIndicator() {
  if (!isAuthPreviewEnabled) return null;
  return <div className="developer-preview-indicator" role="status">Developer preview</div>;
}
