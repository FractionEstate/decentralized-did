import { Drivers, Storage } from "@ionic/storage";

class IonicSession {
  private static readonly drivers = [Drivers.IndexedDB];

  private sessionInstance?: Storage;

  get session() {
    return this.sessionInstance;
  }

  async open(storageName: string): Promise<void> {
    if (!this.session) {
      try {
        console.log(`[IonicSession] Opening storage: ${storageName}`);
        this.sessionInstance = new Storage({
          name: storageName,
          driverOrder: IonicSession.drivers,
        });
        await this.sessionInstance.create();
        console.log(`[IonicSession] ✅ Storage created successfully: ${storageName}`);
      } catch (e) {
        const error = e as { name?: string; message?: string };
        console.error(`[IonicSession] ❌ Failed to create storage: ${storageName}`, error);

        if (error.name === 'NotFoundError') {
          console.error(`🔍 [IonicSession] NotFoundError detected during IndexedDB initialization`);
          console.error(`🔍 [IonicSession] Storage name: ${storageName}`);
          console.error(`🔍 [IonicSession] Driver: IndexedDB`);
        }

        throw e;
      }
    }
  }

  async wipe(_storageName: string): Promise<void> {
    try {
      await this.sessionInstance?.clear();
      console.log(`[IonicSession] ✅ Storage wiped: ${_storageName}`);
    } catch (e) {
      const error = e as { name?: string };

      if (error.name === 'NotFoundError') {
        console.error(`🔍 [IonicSession] NotFoundError on wipe("${_storageName}"):`, e);
      }

      throw e;
    }
  }
}

export { IonicSession };
