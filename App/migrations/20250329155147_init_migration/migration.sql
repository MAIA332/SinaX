-- CreateTable
CREATE TABLE "CachesCollections" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "fields" JSONB NOT NULL,
    "sizeInBytes" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "CachesCollections_pkey" PRIMARY KEY ("id")
);
