/*
  Warnings:

  - You are about to drop the `CachesCollections` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropTable
DROP TABLE "CachesCollections";

-- CreateTable
CREATE TABLE "Cachedcollections" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "fields" JSONB NOT NULL,
    "sizeInBytes" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "record_count" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "Cachedcollections_pkey" PRIMARY KEY ("id")
);
