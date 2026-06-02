// 大文件分片上传工具

export interface ChunkUploadOptions {
  file: File;
  chunkSize?: number;
  onProgress?: (progress: number) => void;
  onChunkComplete?: (chunkIndex: number, totalChunks: number) => void;
  onError?: (error: Error) => void;
  onComplete?: (result: any) => void;
}

export interface ChunkInfo {
  chunkIndex: number;
  chunk: Blob;
  totalChunks: number;
  fileId: string;
  fileName: string;
  fileSize: number;
  fileHash?: string;
}

export class ChunkUploader {
  private file: File;
  private chunkSize: number;
  private fileId: string;
  private totalChunks: number;
  private uploadedChunks: Set<number>;
  private options: ChunkUploadOptions;

  constructor(options: ChunkUploadOptions) {
    this.file = options.file;
    this.chunkSize = options.chunkSize || 5 * 1024 * 1024; // 默认5MB
    this.fileId = this.generateFileId();
    this.totalChunks = Math.ceil(this.file.size / this.chunkSize);
    this.uploadedChunks = new Set();
    this.options = options;
  }

  private generateFileId(): string {
    return `${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }

  private async calculateFileHash(): Promise<string> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const buffer = e.target?.result as ArrayBuffer;
        const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
        resolve(hashHex);
      };
      reader.readAsArrayBuffer(this.file);
    });
  }

  private createChunk(chunkIndex: number): Blob {
    const start = chunkIndex * this.chunkSize;
    const end = Math.min(start + this.chunkSize, this.file.size);
    return this.file.slice(start, end);
  }

  private async uploadChunk(
    chunkInfo: ChunkInfo,
    uploadUrl: string,
  ): Promise<void> {
    const formData = new FormData();
    formData.append("chunk", chunkInfo.chunk);
    formData.append("chunkIndex", chunkInfo.chunkIndex.toString());
    formData.append("totalChunks", chunkInfo.totalChunks.toString());
    formData.append("fileId", chunkInfo.fileId);
    formData.append("fileName", chunkInfo.fileName);
    formData.append("fileSize", chunkInfo.fileSize.toString());

    if (chunkInfo.fileHash) {
      formData.append("fileHash", chunkInfo.fileHash);
    }

    const response = await fetch(uploadUrl, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`分片上传失败: ${response.statusText}`);
    }

    return response.json();
  }

  private updateProgress(): void {
    if (this.options.onProgress) {
      const progress = Math.round(
        (this.uploadedChunks.size / this.totalChunks) * 100,
      );
      this.options.onProgress(progress);
    }
  }

  async upload(uploadUrl: string): Promise<any> {
    try {
      const fileHash = await this.calculateFileHash();

      for (let i = 0; i < this.totalChunks; i++) {
        if (this.uploadedChunks.has(i)) {
          continue;
        }

        const chunk = this.createChunk(i);
        const chunkInfo: ChunkInfo = {
          chunkIndex: i,
          chunk,
          totalChunks: this.totalChunks,
          fileId: this.fileId,
          fileName: this.file.name,
          fileSize: this.file.size,
          fileHash,
        };

        await this.uploadChunk(chunkInfo, uploadUrl);
        this.uploadedChunks.add(i);

        if (this.options.onChunkComplete) {
          this.options.onChunkComplete(i, this.totalChunks);
        }

        this.updateProgress();
      }

      if (this.options.onComplete) {
        const result = {
          fileId: this.fileId,
          fileName: this.file.name,
          fileSize: this.file.size,
          fileHash,
        };
        this.options.onComplete(result);
      }

      return {
        fileId: this.fileId,
        fileName: this.file.name,
        fileSize: this.file.size,
        fileHash,
      };
    } catch (error) {
      if (this.options.onError) {
        this.options.onError(error as Error);
      }
      throw error;
    }
  }

  async resumeUpload(uploadUrl: string): Promise<any> {
    try {
      const fileHash = await this.calculateFileHash();

      for (let i = 0; i < this.totalChunks; i++) {
        if (this.uploadedChunks.has(i)) {
          continue;
        }

        const chunk = this.createChunk(i);
        const chunkInfo: ChunkInfo = {
          chunkIndex: i,
          chunk,
          totalChunks: this.totalChunks,
          fileId: this.fileId,
          fileName: this.file.name,
          fileSize: this.file.size,
          fileHash,
        };

        await this.uploadChunk(chunkInfo, uploadUrl);
        this.uploadedChunks.add(i);

        if (this.options.onChunkComplete) {
          this.options.onChunkComplete(i, this.totalChunks);
        }

        this.updateProgress();
      }

      if (this.options.onComplete) {
        const result = {
          fileId: this.fileId,
          fileName: this.file.name,
          fileSize: this.file.size,
          fileHash,
        };
        this.options.onComplete(result);
      }

      return {
        fileId: this.fileId,
        fileName: this.file.name,
        fileSize: this.file.size,
        fileHash,
      };
    } catch (error) {
      if (this.options.onError) {
        this.options.onError(error as Error);
      }
      throw error;
    }
  }

  pause(): void {
    // 暂停上传，通过不继续上传后续分片实现
  }

  cancel(): void {
    this.uploadedChunks.clear();
  }

  getProgress(): number {
    return Math.round((this.uploadedChunks.size / this.totalChunks) * 100);
  }

  getUploadedChunks(): number[] {
    return Array.from(this.uploadedChunks);
  }
}

export async function uploadFileWithChunks(
  file: File,
  uploadUrl: string,
  options?: Partial<ChunkUploadOptions>,
): Promise<any> {
  const uploader = new ChunkUploader({
    file,
    ...options,
  });

  return uploader.upload(uploadUrl);
}

export async function resumeFileUpload(
  fileId: string,
  uploadedChunks: number[],
  file: File,
  uploadUrl: string,
  options?: Partial<ChunkUploadOptions>,
): Promise<any> {
  const uploader = new ChunkUploader({
    file,
    ...options,
  });

  uploader["fileId"] = fileId;
  uploader["uploadedChunks"] = new Set(uploadedChunks);

  return uploader.resumeUpload(uploadUrl);
}
